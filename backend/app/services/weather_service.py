"""WeatherService: fetches Open-Meteo forecasts for NFL stadium coordinates.

Returns None for indoor stadiums — never show weather chip for controlled environments.
Always requests wind_speed_unit=mph to match the 20 mph TM-09 threshold (Pitfall 5 in RESEARCH.md).

Cache strategy: 6h TTL per team+date. Weather doesn't change meaningfully within a game day.
"""
import json

import httpx
from fastapi import Depends
from redis.asyncio import Redis

from app.core.cache import CacheKey, CacheTTL
from app.core.logging import logger
from app.core.redis import get_redis
from app.data.nfl_stadiums import NFL_STADIUMS, WEATHER_WIND_THRESHOLD_MPH, WEATHER_RAIN_CODE_THRESHOLD

OPEN_METEO_BASE = "https://api.open-meteo.com"

# WMO weather code thresholds
_SNOW_CODE_MIN = 71   # WMO 71–77: snowfall
_SNOW_CODE_MAX = 77
_HEAVY_RAIN_MM_THRESHOLD = 2.5  # mm precipitation in the game hour = heavy rain


class WeatherServiceError(Exception):
    """Raised for non-200 responses from Open-Meteo API."""


def _should_show_weather_chip(wind_mph: float, precipitation_mm: float, weather_code: int) -> bool:
    """Return True if this weather warrants a chip on the player card.

    Thresholds (TM-09):
      - Wind: >= 20 mph
      - Rain: precipitation_mm >= 2.5 mm in game hour OR WMO code >= 63 (moderate/heavy rain)
      - Snow: WMO code 71–77 (any snowfall)
    """
    has_wind = wind_mph >= WEATHER_WIND_THRESHOLD_MPH
    has_heavy_rain = precipitation_mm >= _HEAVY_RAIN_MM_THRESHOLD or weather_code >= WEATHER_RAIN_CODE_THRESHOLD
    has_snow = _SNOW_CODE_MIN <= weather_code <= _SNOW_CODE_MAX
    return has_wind or has_heavy_rain or has_snow


def _extract_kickoff_weather(forecast: dict, game_date: str) -> dict | None:
    """Extract weather at the nearest kickoff hour (13:00 or 16:00 local) from Open-Meteo hourly data.

    If the game_date is not in the forecast window, returns None.
    Returns dict: {wind_mph, precipitation_mm, weather_code, snowfall_mm, has_chip}.
    """
    hourly = forecast.get("hourly", {})
    times = hourly.get("time", [])
    winds = hourly.get("wind_speed_10m", [])
    precip = hourly.get("precipitation", [])
    codes = hourly.get("weather_code", [])
    snowfall = hourly.get("snowfall", [])

    # Target the 1pm slot (13:00) as the primary kickoff proxy
    target_hour = f"{game_date}T13:00"
    if target_hour not in times:
        # Try 4pm slot (most late games)
        target_hour = f"{game_date}T16:00"
    if target_hour not in times:
        return None

    idx = times.index(target_hour)
    wind_mph = winds[idx] if idx < len(winds) else 0.0
    precipitation_mm = precip[idx] if idx < len(precip) else 0.0
    weather_code = codes[idx] if idx < len(codes) else 0
    snowfall_mm = snowfall[idx] if idx < len(snowfall) else 0.0

    return {
        "wind_mph": round(wind_mph, 1),
        "precipitation_mm": round(precipitation_mm, 2),
        "weather_code": weather_code,
        "snowfall_mm": round(snowfall_mm, 2),
        "has_chip": _should_show_weather_chip(wind_mph, precipitation_mm, weather_code),
    }


class WeatherService:
    """Fetches game-day weather for outdoor NFL stadiums from Open-Meteo.

    Indoor stadiums (LV, LAR, LAC, IND, DET, MIN, ATL, ARI, HOU) always return None.
    Inject via get_weather_service() FastAPI dependency.
    """

    def __init__(self, http: httpx.AsyncClient, redis: Redis) -> None:
        self.http = http
        self.redis = redis

    async def get_game_weather(self, team_abbr: str, game_date: str) -> dict | None:
        """Return weather dict for an outdoor stadium, or None for indoor/unknown teams.

        Args:
            team_abbr: NFL team abbreviation (e.g., "KC", "BUF")
            game_date: ISO date string (e.g., "2026-09-07")

        Returns:
            {wind_mph, precipitation_mm, weather_code, snowfall_mm, has_chip} or None
        """
        stadium = NFL_STADIUMS.get(team_abbr.upper())
        if not stadium:
            logger.warning("weather.unknown_team", team_abbr=team_abbr)
            return None
        if stadium["indoor"]:
            logger.info("weather.indoor.skip", team_abbr=team_abbr, stadium=stadium["name"])
            return None

        key = CacheKey.open_meteo_weather(team_abbr.upper(), game_date)
        cached = await self.redis.get(key)
        if cached:
            logger.info("weather.cache.hit", team_abbr=team_abbr, game_date=game_date)
            return json.loads(cached)

        logger.info("weather.fetch", team_abbr=team_abbr, game_date=game_date)
        try:
            r = await self.http.get(
                f"{OPEN_METEO_BASE}/v1/forecast",
                params={
                    "latitude": stadium["lat"],
                    "longitude": stadium["lon"],
                    "hourly": "wind_speed_10m,precipitation,weather_code,snowfall",
                    "wind_speed_unit": "mph",   # CRITICAL: always mph (RESEARCH.md Pitfall 5)
                    "forecast_days": 7,
                },
            )
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WeatherServiceError(f"Open-Meteo returned {exc.response.status_code}") from exc

        weather = _extract_kickoff_weather(r.json(), game_date)
        # Cache even None results to avoid re-fetching for dates outside forecast window
        await self.redis.set(key, json.dumps(weather), ex=CacheTTL.OPEN_METEO)
        return weather


async def get_weather_service(redis: Redis = Depends(get_redis)) -> WeatherService:
    """FastAPI dependency: yields a WeatherService with a shared httpx client."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        yield WeatherService(client, redis)
