"""FastAPI dependency injection: auth guard + league/draft ownership guards."""
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.league import League, LeagueMember
from app.models.user import User

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer JWT and return the authenticated User.

    Raises 401 if token is missing, expired, invalid, or user is not verified.
    This dependency is the primary auth gate on all protected endpoints.
    """
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.get(User, UUID(user_id))
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


async def get_league_for_user(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> League:
    """Resolve a league ID to a League that the current user is a member of.

    Never trust the URL league_id alone — always join through league_members
    filtered by current_user.id. Returns 404 (not 403) to avoid confirming
    the existence of another user's league. Satisfies LC-09.
    """
    result = await db.execute(
        select(League)
        .join(LeagueMember, LeagueMember.league_id == League.id)
        .where(LeagueMember.user_id == current_user.id)
        .where(League.id == league_id)
    )
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league


async def get_draft_for_user(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve draft_id to a Draft the current user is a member of.

    Row-level isolation: joins through league_members to verify membership.
    Returns 404 (not 403) to avoid confirming existence of other users' drafts.
    Satisfies T-4-01 (Spoofing — never reveal draft existence to non-members).
    """
    from app.models.draft import Draft

    result = await db.execute(
        select(Draft)
        .join(LeagueMember, LeagueMember.league_id == Draft.league_id)
        .where(LeagueMember.user_id == current_user.id)
        .where(Draft.id == draft_id)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft
