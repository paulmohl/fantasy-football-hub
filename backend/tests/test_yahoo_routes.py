"""Tests for Yahoo API routes (03-08): /yahoo/leagues and /yahoo/import."""
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.user import User
from app.services.credential_service import CredentialService


def _make_user(db):
    """Create a real User in the DB and return (user, access_token)."""
    import asyncio
    from app.core.security import create_access_token
    user = User(
        email=f"yahoo_{uuid4().hex[:6]}@example.com",
        password_hash=None,
        is_verified=True,
    )
    return user, create_access_token(str(user.id))


@pytest.mark.asyncio
async def test_yahoo_leagues_no_credential(async_client, test_db):
    """GET /yahoo/leagues returns 401 when no Yahoo credential stored."""
    from app.core.security import create_access_token
    user = User(email="no_cred@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))
    resp = await async_client.get(
        "/api/v1/yahoo/leagues",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert "not connected" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_yahoo_leagues_valid_credential(async_client, test_db):
    """GET /yahoo/leagues calls YahooClient with stored token and returns league list."""
    from app.core.security import create_access_token

    user = User(email="yahoo_leagues@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    cred_dict = {
        "access_token": "valid_token",
        "refresh_token": "refresh_token",
        "expires_at": time.time() + 3600,
    }
    await cred_svc.store_credential(user, "yahoo", cred_dict, test_db)
    await test_db.commit()

    token = create_access_token(str(user.id))

    mock_yahoo = MagicMock()
    mock_yahoo.get_game_key = AsyncMock(return_value="nfl.l.2025")
    mock_yahoo.get_user_leagues = AsyncMock(return_value=[{"league_key": "nfl.l.123"}])

    with patch("app.api.v1.yahoo.YahooClient", return_value=mock_yahoo), \
         patch("app.api.v1.yahoo.httpx.AsyncClient") as mock_http_cls:
        mock_http_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_http_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_http_cls.return_value.aclose = AsyncMock()

        resp = await async_client.get(
            "/api/v1/yahoo/leagues",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "leagues" in data
    assert "game_key" in data


@pytest.mark.asyncio
async def test_yahoo_import_empty_list(async_client, test_db):
    """POST /yahoo/import returns 422 when league_ids is empty."""
    from app.core.security import create_access_token

    user = User(email="yahoo_empty@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    cred_dict = {
        "access_token": "t",
        "refresh_token": "r",
        "expires_at": time.time() + 3600,
    }
    await cred_svc.store_credential(user, "yahoo", cred_dict, test_db)
    await test_db.commit()

    token = create_access_token(str(user.id))
    resp = await async_client.post(
        "/api/v1/yahoo/import",
        json={"league_ids": [], "game_key": "nfl.l.2025"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_yahoo_login_unconfigured(async_client):
    """GET /auth/yahoo returns 503 when YAHOO_CLIENT_ID is not set."""
    resp = await async_client.get("/api/v1/auth/yahoo", follow_redirects=False)
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"].lower()
