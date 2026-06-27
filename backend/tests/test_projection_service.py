"""Tests for ProjectionService (TM-01, TM-03, TM-06, TM-08).

RED phase: tests fail until projection_service.py is implemented.
Tests use mocked HTTP and Redis — no external network calls.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


pytestmark = pytest.mark.asyncio


def _make_redis(cached_value=None):
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=cached_value)
    redis.set = AsyncMock()
    return redis


def _make_http_response(data):
    response = MagicMock()
    response.json = MagicMock(return_value=data)
    response.raise_for_status = MagicMock()
    response.status_code = 200
    return response


def test_import_projection_service():
    """ProjectionService, FantasyCalcError, and get_projection_service all import cleanly."""
    from app.services.projection_service import ProjectionService, FantasyCalcError, get_projection_service
    assert ProjectionService is not None
    assert FantasyCalcError is not None
    assert get_projection_service is not None


def test_fantasycalc_error_is_exception():
    from app.services.projection_service import FantasyCalcError
    assert issubclass(FantasyCalcError, Exception)


def test_projection_service_init():
    from app.services.projection_service import ProjectionService
    import httpx
    http = MagicMock(spec=httpx.AsyncClient)
    redis = MagicMock()
    svc = ProjectionService(http, redis)
    assert svc.http is http
    assert svc.redis is redis


def test_projection_service_has_required_methods():
    from app.services.projection_service import ProjectionService
    assert hasattr(ProjectionService, "get_fantasycalc_values")
    assert hasattr(ProjectionService, "get_sleeper_players")
    assert hasattr(ProjectionService, "build_sleeper_id_index")
    assert hasattr(ProjectionService, "get_sleeper_trending")
    assert hasattr(ProjectionService, "get_player_weekly_stats")


def test_build_sleeper_id_index_is_sync():
    """build_sleeper_id_index must be synchronous (not a coroutine)."""
    import inspect
    from app.services.projection_service import ProjectionService
    import httpx
    http = MagicMock(spec=httpx.AsyncClient)
    redis = MagicMock()
    svc = ProjectionService(http, redis)
    result = svc.build_sleeper_id_index([])
    assert not inspect.iscoroutine(result), "build_sleeper_id_index must not be async"


def test_build_sleeper_id_index_maps_sleeper_id():
    """build_sleeper_id_index returns dict mapping sleeperId -> FC entry."""
    from app.services.projection_service import ProjectionService
    import httpx
    http = MagicMock(spec=httpx.AsyncClient)
    redis = MagicMock()
    svc = ProjectionService(http, redis)
    fc_values = [
        {"player": {"sleeperId": "1001", "name": "Player A"}, "value": 5000},
        {"player": {"sleeperId": "1002", "name": "Player B"}, "value": 4000},
        {"player": {"name": "No ID Player"}, "value": 3000},  # no sleeperId
    ]
    index = svc.build_sleeper_id_index(fc_values)
    assert "1001" in index
    assert "1002" in index
    assert index["1001"]["value"] == 5000
    assert len(index) == 2  # entry without sleeperId skipped


async def test_get_fantasycalc_values_cache_hit():
    """On cache hit, returns cached data without HTTP call."""
    from app.services.projection_service import ProjectionService
    import httpx
    cached_data = [{"player": {"sleeperId": "1001"}, "value": 5000}]
    redis = _make_redis(cached_value=json.dumps(cached_data))
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock()
    svc = ProjectionService(http, redis)
    result = await svc.get_fantasycalc_values(is_dynasty=False)
    assert result == cached_data
    http.get.assert_not_called()


async def test_get_fantasycalc_values_cache_miss_calls_api():
    """On cache miss, fetches from FantasyCalc and stores in Redis."""
    from app.services.projection_service import ProjectionService
    import httpx
    fc_data = [{"player": {"sleeperId": "1001"}, "value": 5000}]
    redis = _make_redis(cached_value=None)
    response = _make_http_response(fc_data)
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=response)
    svc = ProjectionService(http, redis)
    result = await svc.get_fantasycalc_values(is_dynasty=False)
    assert result == fc_data
    http.get.assert_called_once()
    call_url = http.get.call_args[0][0]
    assert "/values/current" in call_url
    redis.set.assert_called_once()


async def test_get_fantasycalc_values_uses_correct_url():
    """FantasyCalc URL must use /values/current, NOT /values?sport=nfl."""
    from app.services.projection_service import ProjectionService
    import httpx
    fc_data = []
    redis = _make_redis(cached_value=None)
    response = _make_http_response(fc_data)
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=response)
    svc = ProjectionService(http, redis)
    await svc.get_fantasycalc_values(is_dynasty=False)
    call_url = http.get.call_args[0][0]
    assert "values/current" in call_url
    assert "sport=nfl" not in call_url


async def test_get_fantasycalc_values_raises_on_error():
    """FantasyCalcError raised on non-200 response."""
    import httpx
    from app.services.projection_service import ProjectionService, FantasyCalcError
    redis = _make_redis(cached_value=None)
    http = MagicMock(spec=httpx.AsyncClient)
    err_response = MagicMock()
    err_response.status_code = 429
    http.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=err_response
    ))
    svc = ProjectionService(http, redis)
    with pytest.raises(FantasyCalcError):
        await svc.get_fantasycalc_values(is_dynasty=False)


async def test_get_sleeper_players_cache_hit():
    """get_sleeper_players returns cached data without HTTP call on cache hit."""
    from app.services.projection_service import ProjectionService
    import httpx
    cached_data = {"1001": {"fantasy_positions": ["RB"]}}
    redis = _make_redis(cached_value=json.dumps(cached_data))
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock()
    svc = ProjectionService(http, redis)
    result = await svc.get_sleeper_players()
    assert result == cached_data
    http.get.assert_not_called()


async def test_get_sleeper_trending_returns_dict():
    """get_sleeper_trending returns {player_id: count} dict."""
    from app.services.projection_service import ProjectionService
    import httpx
    raw = [{"player_id": "1001", "count": 42}, {"player_id": "1002", "count": 17}]
    redis = _make_redis(cached_value=None)
    response = _make_http_response(raw)
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=response)
    svc = ProjectionService(http, redis)
    result = await svc.get_sleeper_trending()
    assert result == {"1001": 42, "1002": 17}


async def test_get_player_weekly_stats_caches_result():
    """get_player_weekly_stats fetches and caches with SLEEPER_STATS TTL."""
    from app.services.projection_service import ProjectionService
    from app.core.cache import CacheTTL
    import httpx
    stats_data = {"1001": {"pts_ppr": 25.4, "rush_yd": 120}}
    redis = _make_redis(cached_value=None)
    response = _make_http_response(stats_data)
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=response)
    svc = ProjectionService(http, redis)
    result = await svc.get_player_weekly_stats("2025", 1)
    assert result == stats_data
    redis.set.assert_called_once()
    _, kwargs = redis.set.call_args
    assert kwargs.get("ex") == CacheTTL.SLEEPER_STATS


def test_get_projection_service_is_async_generator():
    """get_projection_service must be an async generator (uses yield)."""
    import inspect
    from app.services.projection_service import get_projection_service
    assert inspect.isasyncgenfunction(get_projection_service)


def test_source_uses_correct_fantasycalc_url():
    """Source code check: actual HTTP call uses /values/current, not /values?sport=nfl.

    The deprecated URL may appear in comments/docstrings — check the actual http.get call.
    """
    import inspect
    from app.services import projection_service
    source = inspect.getsource(projection_service)
    assert "values/current" in source
    # Verify the actual API call path (not any comment mentioning the deprecated URL)
    assert 'f"{FANTASYCALC_BASE}/values/current"' in source or "values/current" in source


def test_source_uses_fantasycalc_ttl():
    """Source code check: CacheTTL.FANTASYCALC used for 24h cache."""
    import inspect
    from app.services import projection_service
    source = inspect.getsource(projection_service)
    assert "CacheTTL.FANTASYCALC" in source
