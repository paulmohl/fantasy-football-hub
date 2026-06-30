"""Tests for YahooClient (03-03)."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.yahoo_client import YahooAuthExpired, YahooClient

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


def _make_http(responses: list) -> httpx.AsyncClient:
    """Return an AsyncClient whose .get/.post are AsyncMocks returning responses in order."""
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(side_effect=responses)
    http.post = AsyncMock(side_effect=responses)
    return http


# ── Test get_user_leagues ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user_leagues_success():
    fixture = _fixture("yahoo_league.json")
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, fixture))
    client = YahooClient(http, "valid_token")
    leagues = await client.get_user_leagues()
    assert isinstance(leagues, list)
    assert len(leagues) == 1
    assert leagues[0]["league_key"] == "461.l.1234"


@pytest.mark.asyncio
async def test_get_user_leagues_401():
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(401))
    client = YahooClient(http, "expired_token")
    with pytest.raises(YahooAuthExpired):
        await client.get_user_leagues()


# ── Test get_game_key ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_game_key_runtime():
    """get_game_key must make an API call and parse game_key from the response."""
    fixture = _fixture("yahoo_league.json")
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, fixture))
    client = YahooClient(http, "valid_token")
    key = await client.get_game_key()
    # Returned from fixture, not hardcoded
    http.get.assert_called_once()
    assert key == "461"


# ── Test get_league_settings ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_league_settings():
    payload = {"fantasy_content": {"league": [{"league_key": "461.l.1234", "settings": {"draft_type": "snake"}}]}}
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, payload))
    client = YahooClient(http, "valid_token")
    result = await client.get_league_settings("461.l.1234")
    assert "fantasy_content" in result


# ── Test get_team_roster ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_team_roster():
    payload = {"fantasy_content": {"team": [{}, {"roster": {"players": {}}}]}}
    http = MagicMock(spec=httpx.AsyncClient)
    http.get = AsyncMock(return_value=_mock_response(200, payload))
    client = YahooClient(http, "valid_token")
    result = await client.get_team_roster("461.l.1234.t.1", week=1)
    assert "fantasy_content" in result


# ── Test refresh_access_token ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_success():
    new_tokens = {"access_token": "new_access", "refresh_token": "new_refresh", "expires_in": 3600}
    http = MagicMock(spec=httpx.AsyncClient)
    http.post = AsyncMock(return_value=_mock_response(200, new_tokens))
    result = await YahooClient.refresh_access_token(http, "old_refresh_token")
    assert result["access_token"] == "new_access"
    assert result["refresh_token"] == "new_refresh"


@pytest.mark.asyncio
async def test_refresh_token_401():
    http = MagicMock(spec=httpx.AsyncClient)
    http.post = AsyncMock(return_value=_mock_response(401))
    with pytest.raises(YahooAuthExpired):
        await YahooClient.refresh_access_token(http, "bad_refresh")


# ── Test Accept header on every request ───────────────────────────────────────

@pytest.mark.asyncio
async def test_accept_json_header():
    """Every GET request must include Accept: application/json."""
    captured_calls = []

    async def capture_get(url, **kwargs):
        captured_calls.append(kwargs.get("headers", {}))
        return _mock_response(200, {"fantasy_content": {}})

    http = MagicMock(spec=httpx.AsyncClient)
    http.get = capture_get
    client = YahooClient(http, "tok")
    await client.get_league_settings("461.l.999")

    assert len(captured_calls) == 1
    assert captured_calls[0].get("Accept") == "application/json"
