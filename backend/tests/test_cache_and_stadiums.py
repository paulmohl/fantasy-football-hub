"""Tests for CacheKey/CacheTTL extensions and NFL stadium data (TM-03, TM-06, TM-09).

RED phase: these tests MUST fail before cache.py and nfl_stadiums.py are extended.
"""
import pytest


def test_cachekey_fantasycalc_values_redraft():
    from app.core.cache import CacheKey
    assert CacheKey.fantasycalc_values(False) == "fantasycalc:values:redraft"


def test_cachekey_fantasycalc_values_dynasty():
    from app.core.cache import CacheKey
    assert CacheKey.fantasycalc_values(True) == "fantasycalc:values:dynasty"


def test_cachekey_sleeper_players_nfl():
    from app.core.cache import CacheKey
    assert CacheKey.sleeper_players_nfl() == "sleeper:players:nfl"


def test_cachekey_sleeper_trending_add():
    from app.core.cache import CacheKey
    assert CacheKey.sleeper_trending_add() == "sleeper:trending:add"


def test_cachekey_sleeper_stats():
    from app.core.cache import CacheKey
    assert CacheKey.sleeper_stats("2025", 1) == "sleeper:stats:2025:1"


def test_cachekey_open_meteo_weather():
    from app.core.cache import CacheKey
    assert CacheKey.open_meteo_weather("KC", "2026-09-07") == "weather:KC:2026-09-07"


def test_cachettl_fantasycalc():
    from app.core.cache import CacheTTL
    assert CacheTTL.FANTASYCALC == 86400


def test_cachettl_sleeper_players():
    from app.core.cache import CacheTTL
    assert CacheTTL.SLEEPER_PLAYERS == 86400


def test_cachettl_sleeper_stats():
    from app.core.cache import CacheTTL
    assert CacheTTL.SLEEPER_STATS == 3600


def test_cachettl_sleeper_trending():
    from app.core.cache import CacheTTL
    assert CacheTTL.SLEEPER_TRENDING == 3600


def test_cachettl_open_meteo():
    from app.core.cache import CacheTTL
    assert CacheTTL.OPEN_METEO == 21600


def test_nfl_stadiums_count():
    from app.data.nfl_stadiums import NFL_STADIUMS
    assert len(NFL_STADIUMS) == 32


def test_nfl_stadiums_lv_indoor():
    from app.data.nfl_stadiums import NFL_STADIUMS
    assert NFL_STADIUMS["LV"]["indoor"] is True


def test_nfl_stadiums_kc_outdoor():
    from app.data.nfl_stadiums import NFL_STADIUMS
    assert NFL_STADIUMS["KC"]["indoor"] is False


def test_nfl_stadiums_all_indoor_teams():
    from app.data.nfl_stadiums import NFL_STADIUMS
    indoor_teams = {"LV", "LAR", "LAC", "IND", "DET", "MIN", "ATL", "ARI", "HOU"}
    for team in indoor_teams:
        assert NFL_STADIUMS[team]["indoor"] is True, f"{team} should be indoor=True"


def test_nfl_stadiums_outdoor_teams():
    from app.data.nfl_stadiums import NFL_STADIUMS
    for team in ("KC", "BUF", "GB"):
        assert NFL_STADIUMS[team]["indoor"] is False, f"{team} should be indoor=False"


def test_weather_wind_threshold():
    from app.data.nfl_stadiums import WEATHER_WIND_THRESHOLD_MPH
    assert WEATHER_WIND_THRESHOLD_MPH == 20
