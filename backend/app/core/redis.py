from redis.asyncio import Redis, from_url

from app.core.config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# TTLs (seconds) — matches ARCHITECTURE.md Section 5
class CacheTTL:
    LEAGUE_SETTINGS = 300       # 5 min — rarely changes mid-season
    ROSTER = 120                # 2 min — changes on waiver days
    PLAYER_METADATA = 86400     # 24 hr — names/teams/positions
    MATCHUP = 60                # 1 min — live scoring
    STANDINGS = 300             # 5 min
    WAIVER = 120                # 2 min
