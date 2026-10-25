"""Credential health check for private ESPN credentials (extension connect flow)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.espn_client import ESPNAuthExpired
from workers.tasks import espn_credential_is_healthy


@pytest.mark.asyncio
async def test_healthy_when_fan_api_answers():
    espn = MagicMock()
    espn.get_fan_leagues = AsyncMock(return_value=[])
    with patch("workers.tasks.ESPNClient", return_value=espn) as cls:
        ok = await espn_credential_is_healthy(MagicMock(), {"swid": "{A}", "espn_s2": "s2", "is_public": False})
    assert ok is True
    espn.get_fan_leagues.assert_awaited_once_with("{A}")
    assert cls.call_args.kwargs == {"swid": "{A}", "espn_s2": "s2"}


@pytest.mark.asyncio
async def test_unhealthy_when_cookies_rejected():
    espn = MagicMock()
    espn.get_fan_leagues = AsyncMock(side_effect=ESPNAuthExpired("expired"))
    with patch("workers.tasks.ESPNClient", return_value=espn):
        ok = await espn_credential_is_healthy(MagicMock(), {"swid": "{A}", "espn_s2": "s2", "is_public": False})
    assert ok is False


@pytest.mark.asyncio
async def test_public_credentials_are_always_healthy_and_never_call_espn():
    with patch("workers.tasks.ESPNClient") as cls:
        ok = await espn_credential_is_healthy(MagicMock(), {"league_id": "1", "is_public": True})
    assert ok is True
    cls.assert_not_called()


@pytest.mark.asyncio
async def test_transient_error_does_not_mark_unhealthy():
    espn = MagicMock()
    espn.get_fan_leagues = AsyncMock(side_effect=RuntimeError("timeout"))
    with patch("workers.tasks.ESPNClient", return_value=espn):
        ok = await espn_credential_is_healthy(MagicMock(), {"swid": "{A}", "espn_s2": "s2", "is_public": False})
    assert ok is True
