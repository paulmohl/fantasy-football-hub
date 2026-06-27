import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Session


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_user_session(user_id: UUID, db: AsyncSession) -> str:
    """Create a 30-day refresh token session. Returns the raw opaque token.
    Caller must set the token as an httpOnly cookie — never return it in JSON body.
    """
    raw_token = secrets.token_urlsafe(48)
    session = Session(
        user_id=user_id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=30),
    )
    db.add(session)
    await db.flush()
    return raw_token


async def verify_refresh_token(raw_token: str, db: AsyncSession) -> Session | None:
    """Return the Session if the raw token hashes to a valid, unexpired row."""
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(Session)
        .where(Session.token_hash == token_hash)
        .where(Session.expires_at > datetime.now(UTC).replace(tzinfo=None))
    )
    return result.scalar_one_or_none()


async def rotate_session(old_raw_token: str, db: AsyncSession) -> str | None:
    """Revoke old session and create a new one. Returns new raw token or None if invalid."""
    session = await verify_refresh_token(old_raw_token, db)
    if not session:
        return None
    user_id = session.user_id
    await db.delete(session)
    await db.flush()
    return await create_user_session(user_id, db)


async def delete_session(raw_token: str, db: AsyncSession) -> None:
    """Delete a session by raw token hash (logout)."""
    session = await verify_refresh_token(raw_token, db)
    if session:
        await db.delete(session)
