"""Tests for WeatherService (TM-09).

Wave 0: stubs — import guard until Wave 1 implements weather_service.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_indoor_no_chip():
    """TM-09: Indoor stadiums return None — no weather chip should be shown."""
    pytest.importorskip("app.services.weather_service")
    from app.services.weather_service import WeatherService
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    svc = WeatherService(http=MagicMock(), redis=mock_redis)
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        svc.get_game_weather("LV", "2026-09-07")  # LV = Allegiant, indoor
    )
    assert result is None, "Indoor stadium must return None"


def test_wind_threshold():
    """TM-09: Wind >= 20 mph triggers chip; wind < 20 mph does not."""
    pytest.importorskip("app.services.weather_service")
    from app.services.weather_service import _should_show_weather_chip
    assert _should_show_weather_chip(wind_mph=20, precipitation_mm=0, weather_code=1) is True
    assert _should_show_weather_chip(wind_mph=19, precipitation_mm=0, weather_code=1) is False


def test_wind_unit_is_mph():
    """TM-09: Ensure the Open-Meteo request includes wind_speed_unit=mph (Pitfall 5)."""
    pytest.importorskip("app.services.weather_service")
    from app.services.weather_service import WeatherService
    import inspect
    src = inspect.getsource(WeatherService.get_game_weather)
    assert "wind_speed_unit" in src and "mph" in src, "Must request wind in mph, not km/h"
