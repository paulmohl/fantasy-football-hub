import httpx

from app.core.config import settings
from app.core.logging import logger


class ESPNAuthExpired(Exception):
    """Raised when ESPN cookies are expired, invalid, or response is suspect."""


class ESPNLeagueNotFound(Exception):
    def __init__(self, league_id: str):
        self.league_id = league_id
        super().__init__(f"ESPN league not found: {league_id}")


FAN_API_BASE = "https://fan.api.espn.com/apis/v2/fans"
FOOTBALL_GAME_ID = 1


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

    async def get_fan_leagues(self, swid: str) -> list[dict]:
        """List the football leagues a SWID belongs to via ESPN's fan API.

        Raises ESPNAuthExpired for 401/403. Entries without a football group are skipped.
        """
        params = {
            "displayEvents": "false",
            "displayHiddenPrefs": "true",
            "context": "fantasy",
            "source": "fan_api_fantasy",
            "useCookies": "true",
            "lang": "en",
        }
        r = await self.http.get(f"{FAN_API_BASE}/{swid}", params=params, cookies=self.cookies)
        if r.status_code in (401, 403):
            raise ESPNAuthExpired("ESPN credentials expired or invalid")
        r.raise_for_status()

        leagues = []
        for pref in r.json().get("preferences") or []:
            entry = (pref.get("metaData") or {}).get("entry") or {}
            if entry.get("gameId") != FOOTBALL_GAME_ID:
                continue
            for group in entry.get("groups") or []:
                if group.get("groupId") is None:
                    continue
                leagues.append(
                    {
                        "league_id": str(group["groupId"]),
                        "name": group.get("groupName") or f"League {group['groupId']}",
                        "season": entry.get("seasonId"),
                    }
                )
        return leagues
