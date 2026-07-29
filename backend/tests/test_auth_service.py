"""Phase 3 integration tests: credential health (MP-06), rate limits (MP-07), keeper extraction (MP-09)."""
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.user import User
from app.services.credential_service import CredentialService
from app.services.espn_service import normalize_espn_scoring
from app.services.yahoo_service import normalize_yahoo_scoring


# ── Group 1: Credential health in /users/me (MP-06) ───────────────────────────

@pytest.mark.asyncio
async def test_get_me_no_credentials_returns_empty_health(async_client, test_db):
    """GET /users/me with no credentials returns credential_health: []"""
    from app.core.security import create_access_token

    user = User(email="health_none@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    token = create_access_token(str(user.id))
    resp = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["credential_health"] == []


@pytest.mark.asyncio
async def test_get_me_with_healthy_yahoo_credential(async_client, test_db):
    """GET /users/me with is_healthy=True Yahoo credential returns healthy entry."""
    from app.core.security import create_access_token

    user = User(email="health_yahoo@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    await cred_svc.store_credential(user, "yahoo", {"access_token": "t", "refresh_token": "r"}, test_db)
    await test_db.commit()

    token = create_access_token(str(user.id))
    resp = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    health = resp.json()["credential_health"]
    assert any(c["platform"] == "yahoo" and c["is_healthy"] is True for c in health)


@pytest.mark.asyncio
async def test_get_me_with_unhealthy_espn_credential(async_client, test_db):
    """GET /users/me with is_healthy=False ESPN credential returns unhealthy entry."""
    from app.core.security import create_access_token

    user = User(email="health_espn@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    await cred_svc.store_credential(user, "espn", {"swid": "s", "espn_s2": "e"}, test_db)
    await test_db.commit()
    await cred_svc.mark_unhealthy(user.id, "espn", test_db)
    await test_db.commit()

    token = create_access_token(str(user.id))
    resp = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    health = resp.json()["credential_health"]
    assert any(c["platform"] == "espn" and c["is_healthy"] is False for c in health)


# ── Group 2: Rate limit 429 response (MP-07) ──────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_yahoo_returns_429_when_exceeded(async_client, test_db, mock_redis):
    """Yahoo route returns 429 with X-Rate-Limited header when count > 200."""
    from app.core.security import create_access_token

    user = User(email="rl_yahoo@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    await cred_svc.store_credential(user, "yahoo", {"access_token": "t", "refresh_token": "r", "expires_at": 9999999999}, test_db)
    await test_db.commit()

    # Simulate rate limit exceeded: INCR returns 201
    mock_redis.incr = AsyncMock(return_value=201)
    mock_redis.get = AsyncMock(return_value=None)

    token = create_access_token(str(user.id))
    resp = await async_client.get("/api/v1/yahoo/leagues", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 429
    assert resp.headers.get("x-rate-limited") == "true"


@pytest.mark.asyncio
async def test_rate_limit_within_budget_returns_200(async_client, test_db, mock_redis):
    """Yahoo route returns 200 when INCR count <= 200 (within budget)."""
    from unittest.mock import patch
    from app.core.security import create_access_token

    user = User(email="rl_ok@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    cred_svc = CredentialService()
    await cred_svc.store_credential(user, "yahoo", {"access_token": "t", "refresh_token": "r", "expires_at": 9999999999}, test_db)
    await test_db.commit()

    mock_redis.incr = AsyncMock(return_value=50)

    token = create_access_token(str(user.id))
    mock_yahoo = MagicMock()
    mock_yahoo.get_game_key = AsyncMock(return_value="nfl.l.2025")
    mock_yahoo.get_user_leagues = AsyncMock(return_value=[])

    with patch("app.api.v1.yahoo.YahooClient", return_value=mock_yahoo), \
         patch("app.api.v1.yahoo.httpx.AsyncClient") as mock_http_cls:
        mock_http_cls.return_value.aclose = AsyncMock()
        resp = await async_client.get("/api/v1/yahoo/leagues", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.headers.get("x-rate-limited") is None


@pytest.mark.asyncio
async def test_rate_limit_espn_budget_100(async_client, test_db, mock_redis):
    """ESPN limit is 100 — count=101 returns 429."""
    from app.core.security import create_access_token

    user = User(email="rl_espn@example.com", password_hash=None, is_verified=True)
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    mock_redis.incr = AsyncMock(return_value=101)
    mock_redis.get = AsyncMock(return_value=None)

    token = create_access_token(str(user.id))
    resp = await async_client.post(
        "/api/v1/espn/public",
        json={"league_id": "42"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 429
    assert resp.headers.get("x-rate-limited") == "true"


# ── Group 3: Keeper field extraction (MP-09) ──────────────────────────────────

def test_yahoo_keeper_extraction_from_fixture():
    """normalize_yahoo_scoring returns keeper_settings.max_keepers from settings_data."""
    settings_data = {
        "fantasy_content": {
            "league": [
                {"league_key": "461.l.1234", "max_keepers": "3"},
                {
                    "settings": {
                        "stat_categories": {
                            "stats": {
                                "0": {"stat": {"stat_id": 4, "value": "0.04"}},
                                "1": {"stat": {"stat_id": 5, "value": "4"}},
                            }
                        },
                        "max_keepers": "3",
                        "keeper_cost_type": "1",
                    }
                },
            ]
        }
    }
    result = normalize_yahoo_scoring(settings_data)
    assert "keeper_settings" in result
    assert result["keeper_settings"]["max_keepers"] == 3


def test_yahoo_unmodeled_rules_populated():
    """Yahoo fixture with unknown stat_id populates keeper_settings.unmodeled_rules list."""
    settings_data = {
        "fantasy_content": {
            "league": [
                {},
                {
                    "settings": {
                        "stat_categories": {
                            "stats": {
                                "0": {"stat": {"stat_id": 9999, "value": "2"}},
                            }
                        }
                    }
                },
            ]
        }
    }
    result = normalize_yahoo_scoring(settings_data)
    assert "yahoo_stat_9999" in result["keeper_settings"]["unmodeled_rules"]


def test_espn_keeper_extraction_from_fixture():
    """normalize_espn_scoring extracts keeperCount from acquisitionSettings."""
    league_data = {
        "settings": {
            "scoringSettings": {"scoringItems": []},
            "acquisitionSettings": {
                "keeperCount": 5,
                "keeperOrderType": 2,
            },
        },
        "teams": [],
    }
    result = normalize_espn_scoring(league_data)
    assert result["keeper_settings"]["max_keepers"] == 5


def test_espn_unmodeled_stat_id_in_list():
    """ESPN fixture with unknown statId populates keeper_settings.unmodeled_rules."""
    league_data = {
        "settings": {
            "scoringSettings": {
                "scoringItems": [
                    {"statId": 9999, "points": 3.0},
                ]
            },
            "acquisitionSettings": {},
        },
        "teams": [],
    }
    result = normalize_espn_scoring(league_data)
    assert "espn_stat_9999" in result["keeper_settings"]["unmodeled_rules"]
