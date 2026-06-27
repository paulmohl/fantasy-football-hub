"""ProjectionService: merges FantasyCalc and Sleeper API data for player value ranking.

Caches all external API calls in Redis per CacheTTL constants:
  - FantasyCalc values: 24h (data changes infrequently)
  - Sleeper player pool: 24h (5MB response; expensive to refetch)
  - Sleeper stats: 1h (per-week, finalizes after game)
  - Sleeper trending: 1h (in-season volume driven)

CRITICAL URLS:
  FantasyCalc: https://api.fantasycalc.com/values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1
  NOT /values?sport=nfl (returns 404 — RESEARCH.md Pitfall 1)

ANTI-PATTERNS (from RESEARCH.md):
  - Do NOT call FantasyCalc from browser; always server-side + cache
  - Do NOT hardcode season; use get_nfl_state() from SleeperClient
  - FantasyCalc returns only top 200 players (redraft); treat missing as value=0
"""
import json

import httpx
from fastapi import Depends
from redis.asyncio import Redis

from app.core.cache import CacheKey, CacheTTL
from app.core.redis import get_redis
from app.core.logging import logger


FANTASYCALC_BASE = "https://api.fantasycalc.com"
SLEEPER_BASE = "https://api.sleeper.app"


class FantasyCalcError(Exception):
    """Raised for non-200 responses from FantasyCalc API."""


class ProjectionService:
    """Merges FantasyCalc trade values and Sleeper player data for lineup optimization.

    Inject via get_projection_service() FastAPI dependency.
    """

    def __init__(self, http: httpx.AsyncClient, redis: Redis) -> None:
        self.http = http
        self.redis = redis

    async def get_fantasycalc_values(self, is_dynasty: bool = False) -> list[dict]:
        """Fetch FantasyCalc player values; cached 24h.

        Returns list of FC player entries. Each entry has player.sleeperId for cross-reference.
        Redraft returns ~200 players; dynasty returns ~460.
        """
        key = CacheKey.fantasycalc_values(is_dynasty)
        cached = await self.redis.get(key)
        if cached:
            logger.info("fantasycalc.cache.hit", is_dynasty=is_dynasty)
            return json.loads(cached)

        logger.info("fantasycalc.fetch", is_dynasty=is_dynasty)
        try:
            r = await self.http.get(
                f"{FANTASYCALC_BASE}/values/current",
                params={
                    "isDynasty": str(is_dynasty).lower(),
                    "numQbs": 1,
                    "numTeams": 12,
                    "ppr": 1,
                },
            )
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FantasyCalcError(f"FantasyCalc returned {exc.response.status_code}") from exc

        data: list[dict] = r.json()
        await self.redis.set(key, json.dumps(data), ex=CacheTTL.FANTASYCALC)
        return data

    async def get_sleeper_players(self) -> dict[str, dict]:
        """Fetch full Sleeper player pool; cached 24h.

        Returns dict keyed by player_id string. ~5MB response.
        Each player has fantasy_positions, injury_status, status, search_rank, depth_chart_order.
        """
        key = CacheKey.sleeper_players_nfl()
        cached = await self.redis.get(key)
        if cached:
            logger.info("sleeper.players.cache.hit")
            return json.loads(cached)

        logger.info("sleeper.players.fetch")
        r = await self.http.get(f"{SLEEPER_BASE}/v1/players/nfl")
        r.raise_for_status()
        data: dict[str, dict] = r.json()
        await self.redis.set(key, json.dumps(data), ex=CacheTTL.SLEEPER_PLAYERS)
        return data

    def build_sleeper_id_index(self, fc_values: list[dict]) -> dict[str, dict]:
        """Build index from Sleeper player_id -> FantasyCalc entry.

        Uses player.sleeperId field on each FC entry as the join key.
        Players without sleeperId are excluded (e.g., IDP-only players).
        """
        return {
            entry["player"]["sleeperId"]: entry
            for entry in fc_values
            if entry.get("player", {}).get("sleeperId")
        }

    async def get_sleeper_trending(self) -> dict[str, int]:
        """Fetch Sleeper trending add counts; cached 1h.

        Returns dict {player_id: count}. Low counts during off-season (see RESEARCH.md Pitfall 7).
        """
        key = CacheKey.sleeper_trending_add()
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        logger.info("sleeper.trending.fetch")
        r = await self.http.get(
            f"{SLEEPER_BASE}/v1/players/nfl/trending/add",
            params={"lookback_hours": 24, "limit": 200},
        )
        r.raise_for_status()
        raw: list[dict] = r.json()
        data = {item["player_id"]: item["count"] for item in raw}
        await self.redis.set(key, json.dumps(data), ex=CacheTTL.SLEEPER_TRENDING)
        return data

    async def get_player_weekly_stats(self, season: str, week: int) -> dict[str, dict]:
        """Fetch Sleeper per-player stats for a given week; cached 1h.

        Returns dict {player_id: {pts_ppr, pts_std, pass_yd, rush_yd, rec_yd, off_snp, ...}}.
        Off-season weeks return sparse or empty data.
        """
        key = CacheKey.sleeper_stats(season, week)
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        logger.info("sleeper.stats.fetch", season=season, week=week)
        r = await self.http.get(f"{SLEEPER_BASE}/v1/stats/nfl/regular/{season}/{week}")
        r.raise_for_status()
        data: dict[str, dict] = r.json()
        await self.redis.set(key, json.dumps(data), ex=CacheTTL.SLEEPER_STATS)
        return data


async def get_projection_service(redis: Redis = Depends(get_redis)) -> ProjectionService:
    """FastAPI dependency: yields a ProjectionService with a shared httpx client."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        yield ProjectionService(client, redis)
