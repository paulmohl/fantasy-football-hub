"""League management endpoints (list, detail, refresh, disconnect).

All endpoints use get_league_for_user dependency which JOINs through league_members
filtered by current_user.id. This satisfies LC-09 row-level isolation.
"""
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey
from app.core.database import get_db
from app.core.deps import get_current_user, get_league_for_user
from app.core.redis import get_redis
from app.models.audit import AuditLog
from app.models.league import League, LeagueMember
from app.models.user import User
from app.services.league_service import refresh_league
from app.services.sleeper_client import SleeperClient, get_sleeper_client

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("/mine")
async def get_my_leagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """LC-06: Return all leagues the current user is connected to."""
    result = await db.execute(
        select(League, LeagueMember)
        .join(LeagueMember, LeagueMember.league_id == League.id)
        .where(LeagueMember.user_id == current_user.id)
        .order_by(LeagueMember.connected_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(league.id),
            "name": league.name,
            "season": league.season,
            "host_platform": league.host_platform,
            "draft_type": league.draft_type,
            "keeper_flag": league.keeper_flag,
            "dynasty_flag": league.dynasty_flag,
            "last_synced_at": league.last_synced_at.isoformat() if league.last_synced_at else None,
            "connected_at": member.connected_at.isoformat(),
        }
        for league, member in rows
    ]


@router.get("/{league_id}")
async def get_league(
    league: League = Depends(get_league_for_user),
):
    """LC-09: Return league detail. 404 if user is not a member."""
    return {
        "id": str(league.id),
        "name": league.name,
        "season": league.season,
        "host_platform": league.host_platform,
        "draft_type": league.draft_type,
        "keeper_flag": league.keeper_flag,
        "dynasty_flag": league.dynasty_flag,
        "scoring_rules": league.scoring_rules,
        "roster_format": league.roster_format,
        "last_synced_at": league.last_synced_at.isoformat() if league.last_synced_at else None,
    }


@router.post("/{league_id}/refresh")
async def refresh(
    league: League = Depends(get_league_for_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    sleeper: SleeperClient = Depends(get_sleeper_client),
):
    """LC-07: Re-pull settings, rosters, and members from Sleeper."""
    cached_state = await redis.get(CacheKey.nfl_state())
    if cached_state:
        nfl_state = json.loads(cached_state)
    else:
        nfl_state = await sleeper.get_nfl_state()
    week = int(nfl_state.get("week", 1))
    updated = await refresh_league(league, db, redis, sleeper, week=week)
    return {
        "id": str(updated.id),
        "last_synced_at": updated.last_synced_at.isoformat() if updated.last_synced_at else None,
    }


@router.delete("/{league_id}/connection", status_code=204)
async def disconnect(
    background_tasks: BackgroundTasks,
    league: League = Depends(get_league_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """LC-11: Delete league_members row. Schedule cache purge after 30 days.

    Does NOT delete the League row itself — other users may still be members.
    Historical cached data is retained 30 days per LC-11 requirement.
    """
    result = await db.execute(
        select(LeagueMember)
        .where(LeagueMember.user_id == current_user.id)
        .where(LeagueMember.league_id == league.id)
    )
    member = result.scalar_one_or_none()
    if member:
        await db.delete(member)

    db.add(AuditLog(
        action="league.disconnect",
        target_type="league",
        target_id=str(league.id),
        user_id=current_user.id,
    ))

    background_tasks.add_task(_schedule_purge, str(league.id))
    return None


async def _schedule_purge(league_id: str) -> None:
    """Enqueue arq job to purge cache after 30 days. Fire-and-forget."""
    try:
        import arq
        from app.core.config import settings
        redis_pool = await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
        await redis_pool.enqueue_job("purge_league_cache", league_id, _defer_by=60 * 60 * 24 * 30)
        await redis_pool.aclose()
    except Exception:
        pass  # Non-critical — TTL-based expiry is the fallback
