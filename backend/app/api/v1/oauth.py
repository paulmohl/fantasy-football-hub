"""Google OAuth2 / OpenID Connect endpoints.

Uses authlib + starlette SessionMiddleware (added in main.py by Plan 04).
SessionMiddleware stores the OAuth state between /google and /google/callback.

CRITICAL: Do not implement PKCE/state manually — authlib handles it automatically.
"""
from datetime import UTC, datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, set_refresh_cookie
from app.models.user import User
from app.services.auth_service import create_user_session
from app.services.credential_service import CredentialService

router = APIRouter(prefix="/auth", tags=["oauth"])

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={"scope": "openid email profile"},
)
oauth.register(
    name="yahoo",
    client_id=settings.yahoo_client_id,
    client_secret=settings.yahoo_client_secret,
    authorize_url="https://api.login.yahoo.com/oauth2/request_auth",
    access_token_url="https://api.login.yahoo.com/oauth2/get_token",
    client_kwargs={"scope": "fspt-w"},
)


@router.get("/google")
async def google_login(request: Request):
    """AUTH-02: Redirect user to Google OAuth consent screen.

    authlib writes the state param to the Starlette session (SessionMiddleware).
    If GOOGLE_CLIENT_ID is empty, return 503 so the endpoint is discoverable
    even without credentials configured.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """AUTH-02: Exchange authorization code for tokens; upsert user; issue JWT.

    After success, redirects to frontend with access_token as a query param.
    The frontend must extract this token and store it in Zustand (not localStorage refresh).
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth authorization failed.")

    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Could not retrieve Google account info.")

    google_sub = user_info["sub"]
    email = user_info["email"]

    # Look up existing user by google_sub first, then by email (account linking)
    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.google_sub = google_sub
        else:
            user = User(email=email, google_sub=google_sub, is_verified=True)
            db.add(user)

    user.is_verified = True
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    raw_refresh = await create_user_session(user.id, db)
    access_token = create_access_token(str(user.id))

    response = RedirectResponse(
        url=f"{settings.app_base_url}/auth/callback?token={access_token}&user_id={user.id}"
    )
    set_refresh_cookie(response, raw_refresh)
    return response


@router.get("/yahoo")
async def yahoo_login(request: Request):
    """MP-01: Redirect to Yahoo OAuth consent screen.

    Returns 503 if YAHOO_CLIENT_ID is not configured.
    """
    if not settings.yahoo_client_id:
        raise HTTPException(
            status_code=503,
            detail="Yahoo OAuth not configured. Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET.",
        )
    return await oauth.yahoo.authorize_redirect(request, settings.yahoo_redirect_uri)


@router.get("/yahoo/callback")
async def yahoo_callback(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """MP-01: Exchange authorization code; store encrypted refresh token; redirect to /connect."""
    try:
        token = await oauth.yahoo.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="Yahoo OAuth authorization failed.")

    credential_dict = {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token", ""),
        "expires_at": token.get("expires_at", 0),
    }
    cred_svc = CredentialService()
    async with db.begin_nested():
        await cred_svc.store_credential(current_user, "yahoo", credential_dict, db)

    return RedirectResponse(url=f"{settings.frontend_url}/connect?platform=yahoo")
