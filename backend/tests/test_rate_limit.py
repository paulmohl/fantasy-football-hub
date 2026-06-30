"""Tests for rate limiting (03-09): rate_limit_check, check_platform_rate_limit, CacheKey."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.cache import CacheKey, CacheTTL
from app.core.rate_limit import (
    PLATFORM_LIMITS,
    RateLimitedWithCache,
    check_platform_rate_limit,
    rate_limit_check,
)


# ── CacheKey tests ─────────────────────────────────────────────────────────────

def test_cache_key_yahoo():
    assert CacheKey.rate_limit_yahoo("abc") == "ratelimit:yahoo:abc"


def test_cache_key_espn():
    assert CacheKey.rate_limit_espn("abc") == "ratelimit:espn:abc"


def test_rate_window_constant():
    assert CacheTTL.RATE_WINDOW == 600


def test_platform_limits():
    assert PLATFORM_LIMITS["yahoo"] == 200
    assert PLATFORM_LIMITS["espn"] == 100
    assert PLATFORM_LIMITS["sleeper"] == 100


# ── rate_limit_check tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_check_within_limit():
    """count=1 → returns True (within limit) and calls expire."""
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()

    result = await rate_limit_check(redis, "test:key", limit=200)
    assert result is True
    redis.expire.assert_called_once_with("test:key", 600)


@pytest.mark.asyncio
async def test_rate_limit_check_at_limit():
    """count=200 for Yahoo limit → True (last allowed request)."""
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=200)
    redis.expire = AsyncMock()

    result = await rate_limit_check(redis, "ratelimit:yahoo:u", limit=200)
    assert result is True
    redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_check_exceeded():
    """count=201 → returns False; expire NOT called."""
    redis = MagicMock()
    redis.incr = AsyncMock(return_value=201)
    redis.expire = AsyncMock()

    result = await rate_limit_check(redis, "ratelimit:yahoo:u", limit=200)
    assert result is False
    redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_first_call_sets_ttl():
    """count==1 → expire called; count==2 → expire not called."""
    redis = MagicMock()
    redis.expire = AsyncMock()

    redis.incr = AsyncMock(return_value=1)
    await rate_limit_check(redis, "k", limit=10)
    redis.expire.assert_called_once()

    redis.expire.reset_mock()
    redis.incr = AsyncMock(return_value=2)
    await rate_limit_check(redis, "k", limit=10)
    redis.expire.assert_not_called()


# ── check_platform_rate_limit dependency tests ─────────────────────────────────

@pytest.mark.asyncio
async def test_within_limit_passes():
    """Dependency with count=50 Yahoo calls → returns None (no exception)."""
    from unittest.mock import patch

    redis = MagicMock()
    redis.incr = AsyncMock(return_value=50)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    request = MagicMock()
    request.url.path = "/api/v1/yahoo/leagues"

    user = MagicMock()
    user.id = "user-1"

    dep = check_platform_rate_limit("yahoo")
    result = await dep(request=request, current_user=user, redis=redis)
    assert result is None


@pytest.mark.asyncio
async def test_yahoo_rate_limit_hit_no_cache():
    """Dependency with count=201 and no cached response → HTTPException 429."""
    from fastapi import HTTPException

    redis = MagicMock()
    redis.incr = AsyncMock(return_value=201)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    request = MagicMock()
    request.url.path = "/api/v1/yahoo/leagues"

    user = MagicMock()
    user.id = "user-1"

    dep = check_platform_rate_limit("yahoo")
    with pytest.raises(HTTPException) as exc_info:
        await dep(request=request, current_user=user, redis=redis)

    assert exc_info.value.status_code == 429
    assert "X-Rate-Limited" in exc_info.value.headers


@pytest.mark.asyncio
async def test_yahoo_rate_limit_hit_with_cache():
    """Dependency with count=201 and Redis has cached response → RateLimitedWithCache raised."""
    cached = json.dumps({"leagues": [{"id": 1}]}).encode()

    redis = MagicMock()
    redis.incr = AsyncMock(return_value=201)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=cached)

    request = MagicMock()
    request.url.path = "/api/v1/yahoo/leagues"

    user = MagicMock()
    user.id = "user-1"

    dep = check_platform_rate_limit("yahoo")
    with pytest.raises(RateLimitedWithCache) as exc_info:
        await dep(request=request, current_user=user, redis=redis)

    assert exc_info.value.cached_data == cached.decode()


@pytest.mark.asyncio
async def test_espn_rate_limit_hit():
    """Dependency with count=101 ESPN calls and no cache → HTTPException 429."""
    from fastapi import HTTPException

    redis = MagicMock()
    redis.incr = AsyncMock(return_value=101)
    redis.expire = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    request = MagicMock()
    request.url.path = "/api/v1/espn/connect"

    user = MagicMock()
    user.id = "user-2"

    dep = check_platform_rate_limit("espn")
    with pytest.raises(HTTPException) as exc_info:
        await dep(request=request, current_user=user, redis=redis)

    assert exc_info.value.status_code == 429
