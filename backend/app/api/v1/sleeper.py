"""Sleeper API proxy endpoints.

All Sleeper API calls go through here — never from the browser directly.
Cache username lookups and league lists in Redis to reduce Sleeper traffic.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey, CacheTTL
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.services.league_service import import_league
from app.services.sleeper_client import SleeperClient, SleeperNotFound, get_sleeper_client

router = APIRouter(prefix="/sleeper", tags=["sleeper"])


@router.get("/lookup")
async def lookup(
    username: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    sleeper: SleeperClient = Depends(get_sleeper_client),
):
    """LC-01: Look up Sleeper user and return their leagues.

    Caches user lookup (5 min) and league list (10 min) in Redis.
    """
    normalized = username.strip().lower()

    cached_user = await redis.get(CacheKey.sleeper_user(normalized))
    if cached_user:
        user_data = json.loads(cached_user)
    else:
        try:
            user_data = await sleeper.get_user(normalized)
        except SleeperNotFound:
            raise HTTPException(
                status_code=404,
                detail="That username doesn't exist on Sleeper. Double-check the spelling and try again.",
            )
        await redis.set(CacheKey.sleeper_user(normalized), json.dumps(user_data), ex=CacheTTL.SLEEPER_USER)

    sleeper_user_id = user_data["user_id"]

    cached_state = await redis.get(CacheKey.nfl_state())
    if cached_state:
        nfl_state = json.loads(cached_state)
    else:
        nfl_state = await sleeper.get_nfl_state()
        await redis.set(CacheKey.nfl_state(), json.dumps(nfl_state), ex=CacheTTL.NFL_STATE)
    season = nfl_state["season"]

    cached_leagues = await redis.get(CacheKey.sleeper_leagues(sleeper_user_id, season))
    if cached_leagues:
        leagues = json.loads(cached_leagues)
    else:
        leagues = await sleeper.get_leagues(sleeper_user_id, season)
        await redis.set(
            CacheKey.sleeper_leagues(sleeper_user_id, season),
            json.dumps(leagues),
            ex=CacheTTL.SLEEPER_LEAGUES,
        )

    if not leagues:
        raise HTTPException(
            status_code=422,
            detail="That account has no active leagues. Try a different username or reach out to your commissioner.",
        )

    return {"user": user_data, "leagues": leagues, "season": season}


class ImportRequest(BaseModel):
    league_ids: list[str]


@router.post("/import")
async def import_leagues(
    body: ImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    sleeper: SleeperClient = Depends(get_sleeper_client),
):
    """LC-02, LC-03, LC-04, LC-05: Import one or more Sleeper leagues.

    Each league is imported atomically — one failure does not roll back others.
    Returns list of imported league summaries.
    """
    if not body.league_ids:
        raise HTTPException(status_code=422, detail="Select at least one league to import.")

    cached_state = await redis.get(CacheKey.nfl_state())
    if cached_state:
        nfl_state = json.loads(cached_state)
    else:
        nfl_state = await sleeper.get_nfl_state()
        await redis.set(CacheKey.nfl_state(), json.dumps(nfl_state), ex=CacheTTL.NFL_STATE)
    week = int(nfl_state.get("week", 1))

    results = []
    errors = []
    for league_id in body.league_ids:
        try:
            league = await import_league(league_id, current_user, db, redis, sleeper, week=week)
            results.append({
                "id": str(league.id),
                "name": league.name,
                "season": league.season,
                "draft_type": league.draft_type,
                "keeper_flag": league.keeper_flag,
                "dynasty_flag": league.dynasty_flag,
            })
        except Exception as e:
            errors.append({"league_id": league_id, "error": str(e)})

    if errors and not results:
        raise HTTPException(status_code=502, detail=f"Import failed: {errors[0]['error']}")

    return {"imported": results, "errors": errors}
