"""Async HTTP client wrapper for the Sleeper public API.

All endpoints are public — no auth required.
Rate limit: 1000 req/min IP-level (Sleeper); we enforce 100 req/user/min via Redis.

CRITICAL: Always lowercase the username before calling get_user (Pitfall 6).
CRITICAL: Always fetch current season from get_nfl_state, never hardcode (Pitfall 4).
"""
import httpx

from app.core.config import settings
from app.core.logging import logger


class SleeperNotFound(Exception):
    """Raised when Sleeper API returns 404 for a user or resource."""
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Sleeper resource not found: {identifier}")


class SleeperAPIError(Exception):
    """Raised for non-404 Sleeper API errors."""


class SleeperClient:
    """Wrapper around the Sleeper REST API.

    Inject an httpx.AsyncClient for testability — use get_sleeper_client() in FastAPI.
    """

    def __init__(self, http: httpx.AsyncClient):
        self.http = http
        self.base = settings.sleeper_api_base

    async def get_user(self, username: str) -> dict:
        """Look up a Sleeper user by username. Lowercases username before calling API.

        Returns: {user_id, username, display_name, avatar}
        Raises: SleeperNotFound if 404; httpx.HTTPStatusError for other errors.
        """
        normalized = username.strip().lower()
        logger.info("sleeper.get_user", username=normalized)
        r = await self.http.get(f"{self.base}/user/{normalized}")
        if r.status_code == 404:
            raise SleeperNotFound(normalized)
        r.raise_for_status()
        return r.json()

    async def get_leagues(self, user_id: str, season: str) -> list[dict]:
        """Fetch all NFL leagues for a Sleeper user_id in a given season.

        Returns list of league objects (league_id, name, status, total_rosters, season, avatar).
        """
        r = await self.http.get(f"{self.base}/user/{user_id}/leagues/nfl/{season}")
        r.raise_for_status()
        return r.json() or []

    async def get_league(self, league_id: str) -> dict:
        """Fetch full league detail including scoring_settings and roster_positions."""
        r = await self.http.get(f"{self.base}/league/{league_id}")
        r.raise_for_status()
        return r.json()

    async def get_rosters(self, league_id: str) -> list[dict]:
        """Fetch all rosters for a league.

        Returns list of {roster_id, owner_id, starters, players, settings}.
        """
        r = await self.http.get(f"{self.base}/league/{league_id}/rosters")
        r.raise_for_status()
        return r.json() or []

    async def get_users(self, league_id: str) -> list[dict]:
        """Fetch all member profiles for a league.

        Returns list of {user_id, username, display_name, avatar, metadata, is_owner}.
        """
        r = await self.http.get(f"{self.base}/league/{league_id}/users")
        r.raise_for_status()
        return r.json() or []

    async def get_nfl_state(self) -> dict:
        """Fetch current NFL state including active season string.

        Returns {season, week, season_type}. season is a string like "2025".
        Cache this — TTL 1 hour (CacheTTL.NFL_STATE).
        """
        r = await self.http.get(f"{self.base}/state/nfl")
        r.raise_for_status()
        return r.json()

    async def get_league_matchups(self, league_id: str, week: int) -> list[dict]:
        """Fetch matchup data for a league week.

        Returns list of {roster_id, matchup_id, points, players, starters}.
        Two entries sharing the same matchup_id are head-to-head opponents.
        """
        r = await self.http.get(f"{self.base}/league/{league_id}/matchups/{week}")
        r.raise_for_status()
        return r.json() or []


async def get_sleeper_client():
    """FastAPI dependency that provides a SleeperClient with a managed httpx client."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield SleeperClient(client)
