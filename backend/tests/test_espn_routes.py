"""Tests for ESPN API routes (03-08): /espn/connect and /espn/public."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.user import User


def _make_league_stub(name="Test League"):
    league = MagicMock()
    league.id = uuid4()
    league.name = name
    return league


@pytest.mark.asyncio
async def test_espn_connect_invalid_cookies(async_client, test_db):
    """POST /espn/connect returns 401 when ESPN cookies are rejected."""
    from app.core.security import create_access_token
    from app.services.espn_client import ESPNAuthExpired

    user = User(email="espn_bad_cookie@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))

    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(side_effect=ESPNAuthExpired("Auth expired"))

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/connect",
            json={"swid": "bad-swid", "espn_s2": "bad-s2", "league_id": "123"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_espn_connect_league_not_found(async_client, test_db):
    """POST /espn/connect returns 404 when league ID doesn't exist."""
    from app.core.security import create_access_token
    from app.services.espn_client import ESPNLeagueNotFound

    user = User(email="espn_404@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))

    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(side_effect=ESPNLeagueNotFound("999"))

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/connect",
            json={"swid": "swid", "espn_s2": "s2", "league_id": "999"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_espn_connect_success(async_client, test_db):
    """POST /espn/connect stores credential and returns league info on success."""
    from app.core.security import create_access_token

    user = User(email="espn_ok@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))
    league_stub = _make_league_stub("ESPN Champions")

    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(return_value={"teams": [{"id": 1}]})

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.import_espn_league", AsyncMock(return_value=league_stub)), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/connect",
            json={"swid": "valid-swid", "espn_s2": "valid-s2", "league_id": "42"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ESPN Champions"
    assert data["platform"] == "espn"
    assert data["is_public"] is False


@pytest.mark.asyncio
async def test_espn_public_success(async_client, test_db):
    """POST /espn/public imports league without cookies."""
    from app.core.security import create_access_token

    user = User(email="espn_pub@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))
    league_stub = _make_league_stub("Public League")

    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(return_value={"teams": [{"id": 1}]})

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.import_espn_league", AsyncMock(return_value=league_stub)), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/public",
            json={"league_id": "77"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_public"] is True


@pytest.mark.asyncio
async def test_espn_public_requires_cookie_returns_403(async_client, test_db):
    """POST /espn/public returns 403 when league is private (ESPNAuthExpired on no-cookie)."""
    from app.core.security import create_access_token
    from app.services.espn_client import ESPNAuthExpired

    user = User(email="espn_priv@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))

    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(side_effect=ESPNAuthExpired("Private league"))

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/public",
            json={"league_id": "55"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 403


# ── /espn/leagues (extension connect flow) ────────────────────────────────────

async def _verified_user_token(test_db, email):
    from app.core.security import create_access_token

    user = User(email=email, password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return create_access_token(str(user.id))


@pytest.mark.asyncio
async def test_espn_leagues_returns_list(async_client, test_db):
    token = await _verified_user_token(test_db, "espn_leagues_ok@example.com")
    mock_espn = MagicMock()
    mock_espn.get_fan_leagues = AsyncMock(
        return_value=[{"league_id": "1409037", "name": "Sunday Degenerates", "season": 2026}]
    )

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/leagues",
            json={"swid": "{ABC}", "espn_s2": "AE%2Bx"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json() == {
        "leagues": [{"league_id": "1409037", "name": "Sunday Degenerates", "season": 2026}]
    }
    mock_espn.get_fan_leagues.assert_awaited_once_with("{ABC}")


@pytest.mark.asyncio
async def test_espn_leagues_expired_cookies_401(async_client, test_db):
    from app.services.espn_client import ESPNAuthExpired

    token = await _verified_user_token(test_db, "espn_leagues_401@example.com")
    mock_espn = MagicMock()
    mock_espn.get_fan_leagues = AsyncMock(side_effect=ESPNAuthExpired("expired"))

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/leagues",
            json={"swid": "bad", "espn_s2": "bad"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_espn_leagues_requires_auth(async_client):
    resp = await async_client.post("/v1/espn/leagues", json={"swid": "a", "espn_s2": "b"})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_espn_connect_stores_league_id(async_client, test_db):
    token = await _verified_user_token(test_db, "espn_store_lid@example.com")
    mock_espn = MagicMock()
    mock_espn.get_league = AsyncMock(return_value={"teams": [{"id": 1}]})
    store = AsyncMock()

    with patch("app.api.v1.espn.ESPNClient", return_value=mock_espn), \
         patch("app.api.v1.espn.import_espn_league", AsyncMock(return_value=_make_league_stub())), \
         patch("app.api.v1.espn.CredentialService") as cred_cls, \
         patch("app.api.v1.espn.httpx.AsyncClient") as mock_http:
        cred_cls.return_value.store_credential = store
        mock_http.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http.return_value.__aexit__ = AsyncMock(return_value=None)

        resp = await async_client.post(
            "/v1/espn/connect",
            json={"swid": "{ABC}", "espn_s2": "AE%2Bx", "league_id": "1409037"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    stored = store.await_args.args[2]
    assert stored == {"swid": "{ABC}", "espn_s2": "AE%2Bx", "league_id": "1409037", "is_public": False}
