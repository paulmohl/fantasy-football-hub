import httpx

from app.core.config import settings
from app.core.logging import logger


class ESPNAuthExpired(Exception):
    """Raised when ESPN cookies are expired, invalid, or response is suspect."""


class ESPNLeagueNotFound(Exception):
    def __init__(self, league_id: str):
        self.league_id = league_id
        super().__init__(f"ESPN league not found: {league_id}")


class ESPNClient:
    """Thin async wrapper for the unofficial ESPN Fantasy Football API.

    Private leagues: pass swid and espn_s2 cookies.
    Public leagues: pass swid=None, espn_s2=None.
    Base URL stored in settings.espn_api_base — update .env if ESPN changes domains.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        swid: str | None = None,
        espn_s2: str | None = None,
    ):
        self.http = http
        self.base = settings.espn_api_base
        self.cookies: dict[str, str] = {}
        if swid and espn_s2:
            self.cookies = {"SWID": swid, "espn_s2": espn_s2}

    async def get_league(self, league_id: str, year: int) -> dict:
        """Fetch full league data for one season using all relevant views.

        Raises ESPNAuthExpired for 401/403 or empty response.
        Raises ESPNLeagueNotFound for 404.
        """
        views = ["mSettings", "mRoster", "mTeam", "mMatchupScore", "mStandings"]
        params = [("view", v) for v in views]
        url = f"{self.base}/seasons/{year}/segments/0/leagues/{league_id}"
        logger.info("espn.get_league", league_id=league_id, year=year, is_private=bool(self.cookies))

        r = await self.http.get(url, params=params, cookies=self.cookies)

        if r.status_code in (401, 403):
            raise ESPNAuthExpired(f"ESPN credentials expired or invalid for league {league_id}")
        if r.status_code == 404:
            raise ESPNLeagueNotFound(league_id)
        r.raise_for_status()

        data = r.json()
        teams = data.get("teams")
        if not teams:
            raise ESPNAuthExpired(
                f"ESPN returned empty teams for league {league_id} — cookies likely expired"
            )
        return data

    async def get_league_settings(self, league_id: str, year: int) -> dict:
        """Fetch only mSettings view — lighter call for keeper/scoring rule extraction."""
        url = f"{self.base}/seasons/{year}/segments/0/leagues/{league_id}"
        r = await self.http.get(url, params=[("view", "mSettings")], cookies=self.cookies)
        if r.status_code in (401, 403):
            raise ESPNAuthExpired("ESPN credentials expired")
        if r.status_code == 404:
            raise ESPNLeagueNotFound(league_id)
        r.raise_for_status()
        return r.json()
