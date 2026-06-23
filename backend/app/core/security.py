import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Response
from itsdangerous import URLSafeTimedSerializer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except (ExpiredSignatureError, InvalidTokenError):
        return None


def create_email_token(email: str, salt: str = "email-verify") -> str:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    return s.dumps(email, salt=salt)


def verify_email_token(token: str, salt: str = "email-verify", max_age: int = 86400) -> str | None:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    try:
        return s.loads(token, salt=salt, max_age=max_age)
    except Exception:
        return None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/api/v1/auth/refresh",
    )
