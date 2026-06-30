from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.credential import UserCredential
from app.models.league import LeagueMember
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AUTH-04: Return current user info including has_leagues flag and credential health."""
    result = await db.execute(
        select(func.count()).select_from(LeagueMember).where(LeagueMember.user_id == current_user.id)
    )
    league_count = result.scalar() or 0

    cred_result = await db.execute(
        select(UserCredential).where(UserCredential.user_id == current_user.id)
    )
    credentials = cred_result.scalars().all()
    credential_health = [
        {"platform": c.platform, "is_healthy": c.is_healthy}
        for c in credentials
    ]

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "has_leagues": league_count > 0,
        "created_at": current_user.created_at.isoformat(),
        "credential_health": credential_health,
    }
