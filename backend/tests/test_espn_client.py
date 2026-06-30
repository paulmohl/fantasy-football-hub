"""Tests for ESPNClient (03-04)."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.espn_client import ESPNAuthExpired, ESPNClient, ESPNLeagueNotFound

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _mock_response(status_code: int = 200, json_body: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_body or {})
    if status_code >= 400:
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


# ── Private auth (with cookies) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_espn_private_connect():
    fixture = _fixture("espn_league.json")
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, fixture))
    client = ESPNClient(http, swid="{ABC-123}", espn_s2="long_token_value")
    result = await client.get_league("336541", 2025)
    assert "teams" in result
    assert len(result["teams"]) > 0


@pytest.mark.asyncio
async def test_espn_public_connect():
    """Public league: no cookies sent, still returns teams."""
    fixture = _fixture("espn_league.json")
    captured = {}

    async def capture_get(url, **kwargs):
        captured["cookies"] = kwargs.get("cookies", {})
        return _mock_response(200, fixture)

    http = MagicMock(spec=httpx.AsyncClient)
    http.get = capture_get
    client = ESPNClient(http)  # no swid/espn_s2
    result = await client.get_league("336541", 2025)
    assert "teams" in result
    assert captured["cookies"] == {}


# ── Auth failures ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_espn_401_raises_auth_expired():
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(401))
    client = ESPNClient(http, swid="{x}", espn_s2="y")
    with pytest.raises(ESPNAuthExpired):
        await client.get_league("99999", 2025)


@pytest.mark.asyncio
async def test_espn_403_raises_auth_expired():
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(403))
    client = ESPNClient(http, swid="{x}", espn_s2="y")
    with pytest.raises(ESPNAuthExpired):
        await client.get_league("99999", 2025)


@pytest.mark.asyncio
async def test_espn_404_raises_league_not_found():
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(404))
    client = ESPNClient(http)
    with pytest.raises(ESPNLeagueNotFound) as exc_info:
        await client.get_league("deadbeef", 2025)
    assert exc_info.value.league_id == "deadbeef"


# ── Pitfall 8: empty 200 ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_espn_empty_200_raises_auth_expired():
    """A 200 with no 'teams' key means private league with expired cookies."""
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, {"settings": {}}))
    client = ESPNClient(http, swid="{x}", espn_s2="y")
    with pytest.raises(ESPNAuthExpired):
        await client.get_league("336541", 2025)


@pytest.mark.asyncio
async def test_expired_cookies_empty_teams_list():
    """200 with teams=[] (empty list) also means auth expired."""
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, {"teams": [], "settings": {}}))
    client = ESPNClient(http, swid="{x}", espn_s2="y")
    with pytest.raises(ESPNAuthExpired):
        await client.get_league("336541", 2025)


# ── Required views in params ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_views_in_request():
    """get_league must pass all required view params."""
    fixture = _fixture("espn_league.json")
    captured = {}

    async def capture_get(url, **kwargs):
        captured["params"] = kwargs.get("params", [])
        return _mock_response(200, fixture)

    http = MagicMock(spec=httpx.AsyncClient)
    http.get = capture_get
    client = ESPNClient(http)
    await client.get_league("336541", 2025)

    view_values = [v for k, v in captured["params"] if k == "view"]
    for expected in ("mSettings", "mRoster", "mTeam", "mStandings"):
        assert expected in view_values, f"Missing view param: {expected}"


# ── Base URL from settings ────────────────────────────────────────────────────

def test_base_url_from_settings():
    """ESPNClient.base must come from settings.espn_api_base, not a hardcoded string."""
    from app.core.config import settings
    http = MagicMock(spec=httpx.AsyncClient)
    client = ESPNClient(http)
    assert client.base == settings.espn_api_base
    assert "lm-api-reads" in client.base
