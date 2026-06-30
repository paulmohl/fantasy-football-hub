import base64

import httpx

from app.core.config import settings
from app.core.logging import logger

YAHOO_FANTASY_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"


class YahooAuthExpired(Exception):
    """Raised when Yahoo returns 401 — token is expired or revoked."""


class YahooAPIError(Exception):
    """Raised for non-auth Yahoo API errors."""


class YahooClient:
    """Thin async wrapper for the Yahoo Fantasy Sports API.

    Inject an httpx.AsyncClient for testability.
    access_token must be fresh — callers refresh before instantiating if expires_at < now+300s.
    """

    def __init__(self, http: httpx.AsyncClient, access_token: str):
        self.http = http
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def _get(self, url: str, params: dict | None = None) -> dict:
        r = await self.http.get(url, headers=self.headers, params=params or {})
        if r.status_code == 401:
            raise YahooAuthExpired("Yahoo access token expired or revoked")
        r.raise_for_status()
        return r.json()

    async def get_game_key(self) -> str:
        """Fetch the current NFL game key from Yahoo — never hardcoded."""
        data = await self._get(f"{YAHOO_FANTASY_BASE}/games;game_codes=nfl")
        games = data.get("fantasy_content", {}).get("games", {})
        game = games.get("0", {}).get("game", [{}])
        return str(game[0].get("game_key", "461"))

    async def get_user_leagues(self) -> list[dict]:
        """Return all NFL leagues for the authenticated user in the current season."""
        url = f"{YAHOO_FANTASY_BASE}/users;use_login=1/games;game_codes=nfl/leagues"
        data = await self._get(url)
        leagues_raw = (
            data.get("fantasy_content", {})
            .get("users", {})
            .get("0", {})
            .get("user", [{}, {}])[1]
            .get("games", {})
        )
        result = []
        i = 0
        while str(i) in leagues_raw:
            game = leagues_raw[str(i)].get("game", [{}, {}])
            leagues_node = game[1].get("leagues", {})
            j = 0
            while str(j) in leagues_node:
                league_data = leagues_node[str(j)].get("league", [{}])
                if league_data:
                    result.append(league_data[0])
                j += 1
            i += 1
        return result

    async def get_league_settings(self, league_key: str) -> dict:
        """Fetch settings including scoring, roster positions, keeper rules."""
        url = f"{YAHOO_FANTASY_BASE}/league/{league_key}/settings;out=stat_categories"
        return await self._get(url)

    async def get_league_teams(self, league_key: str) -> dict:
        url = f"{YAHOO_FANTASY_BASE}/league/{league_key}/teams"
        return await self._get(url)

    async def get_team_roster(self, team_key: str, week: int) -> dict:
        """team_key format: {game_key}.l.{league_id}.t.{team_id}"""
        url = f"{YAHOO_FANTASY_BASE}/team/{team_key}/roster;type=week;week={week}"
        return await self._get(url)

    @staticmethod
    async def refresh_access_token(
        http: httpx.AsyncClient,
        refresh_token: str,
    ) -> dict:
        """Exchange refresh_token for new access_token and new refresh_token.

        Returns: {"access_token": str, "refresh_token": str, "expires_in": int}
        Raises YahooAuthExpired if refresh is rejected.
        """
        creds = base64.b64encode(
            f"{settings.yahoo_client_id}:{settings.yahoo_client_secret}".encode()
        ).decode()
        r = await http.post(
            YAHOO_TOKEN_URL,
            headers={"Authorization": f"Basic {creds}"},
            data={
                "grant_type": "refresh_token",
                "redirect_uri": settings.yahoo_redirect_uri,
                "refresh_token": refresh_token,
            },
        )
        if r.status_code == 401:
            raise YahooAuthExpired("Yahoo refresh token rejected — user must re-authorize")
        r.raise_for_status()
        return r.json()


async def get_yahoo_client(access_token: str) -> YahooClient:
    """FastAPI dependency factory — creates a YahooClient with a shared httpx session."""
    http = httpx.AsyncClient(timeout=15.0)
    return YahooClient(http, access_token)
