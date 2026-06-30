"""Per-platform rate limiting for external fantasy API calls (MP-07).

Fixed-window strategy: Redis INCR + EXPIRE per user per platform.
When limit is exceeded:
  - If Redis holds a cached response → RateLimitedWithCache (app handler returns 200 + X-Rate-Limited header)
  - Otherwise → HTTPException 429 with X-Rate-Limited: true header
"""
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from app.core.cache import CacheKey, CacheTTL
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models.user import User

PLATFORM_LIMITS = {
    "yahoo": 200,
    "espn": 100,
    "sleeper": 100,
}


class RateLimitedWithCache(Exception):
    """Raised when rate-limited but a cached response exists.

    The app-level handler in main.py catches this and returns
    200 + X-Rate-Limited: true header + cached body so the frontend
    can show stale data gracefully with a toast notification.
    """

    def __init__(self, cached_data: str):
        self.cached_data = cached_data


async def rate_limit_check(redis: Redis, key: str, limit: int, window: int = CacheTTL.RATE_WINDOW) -> bool:
    """Atomic fixed-window check: INCR then EXPIRE on first call.

    Returns True if within limit; False if exceeded.
    TTL is only set on the first call in a window (count == 1).
    """
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)
    return count <= limit


def check_platform_rate_limit(platform: str):
    """FastAPI dependency factory for per-platform rate limiting (MP-07).

    Usage:
        @router.get("/leagues")
        async def list_yahoo_leagues(
            _: None = Depends(check_platform_rate_limit("yahoo")),
            ...
        ):
    """
    limit = PLATFORM_LIMITS.get(platform, 100)

    async def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
        redis: Redis = Depends(get_redis),
    ) -> None:
        key_fn = getattr(CacheKey, f"rate_limit_{platform}", None)
        if key_fn is None:
            return
        key = key_fn(str(current_user.id))
        within_limit = await rate_limit_check(redis, key, limit)
        if not within_limit:
            cache_key = f"resp:{platform}:{str(current_user.id)}:{request.url.path}"
            cached_bytes = await redis.get(cache_key)
            if cached_bytes:
                raise RateLimitedWithCache(cached_bytes.decode())
            raise HTTPException(
                status_code=429,
                detail=f"{platform.capitalize()} rate limit reached. Try again in a few minutes.",
                headers={"X-Rate-Limited": "true"},
            )

    return _check
