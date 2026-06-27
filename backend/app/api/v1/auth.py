from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_email_token,
    hash_password,
    set_refresh_cookie,
    verify_email_token,
    verify_password,
)
from app.models.user import User
from app.services.auth_service import (
    create_user_session,
    delete_session,
    rotate_session,
    verify_refresh_token,
)
from app.services.email_service import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


@router.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """AUTH-01: Create unverified user and send verification email."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()
    token = create_email_token(body.email, salt="email-verify")
    background_tasks.add_task(send_verification_email, body.email, token)
    return {"email": user.email, "is_verified": user.is_verified}


@router.get("/verify-email")
async def verify_email(
    token: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """AUTH-01: Flip is_verified=True and return access token."""
    email = verify_email_token(token, salt="email-verify", max_age=86400)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_verified = True
    await db.flush()
    raw_refresh = await create_user_session(user.id, db)
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)), user_id=str(user.id))


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """AUTH-01: Verify password, enforce is_verified, issue tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_verified:
        raise HTTPException(status_code=401, detail="Please verify your email before signing in.")
    user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
    raw_refresh = await create_user_session(user.id, db)
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)), user_id=str(user.id))


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and return new access token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token.")
    session = await verify_refresh_token(refresh_token, db)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    new_raw = await rotate_session(refresh_token, db)
    if not new_raw:
        raise HTTPException(status_code=401, detail="Session rotation failed.")
    set_refresh_cookie(response, new_raw)
    return TokenResponse(
        access_token=create_access_token(str(session.user_id)),
        user_id=str(session.user_id),
    )


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Delete session and clear cookie."""
    if refresh_token:
        await delete_session(refresh_token, db)
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    return None


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """AUTH-03: Send reset email. Always returns 200 to avoid enumeration."""
    email = body.get("email", "")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        token = create_email_token(email, salt="password-reset")
        background_tasks.add_task(send_password_reset_email, email, token)
    return {"message": "Reset link sent — check your inbox."}


@router.post("/reset-password")
async def reset_password(body: dict, db: AsyncSession = Depends(get_db)):
    """AUTH-03: Verify reset token and update password hash."""
    token = body.get("token", "")
    new_password = body.get("new_password", "")
    if len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
    email = verify_email_token(token, salt="password-reset", max_age=3600)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.password_hash = hash_password(new_password)
    return {"message": "Password updated."}


@router.post("/resend-verification")
async def resend_verification(
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email. Always 200 to avoid enumeration."""
    email = body.get("email", "")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and not user.is_verified:
        token = create_email_token(email, salt="email-verify")
        background_tasks.add_task(send_verification_email, email, token)
    return {"message": "Verification email sent if account exists."}
