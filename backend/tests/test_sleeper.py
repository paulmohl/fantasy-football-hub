"""Tests for LC-01 (Sleeper lookup) and LC-08 (error handling)."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.sleeper_client import SleeperNotFound, get_sleeper_client


def make_mock_sleeper():
    client = MagicMock()
    client.get_user = AsyncMock(return_value={"user_id": "u123", "username": "testuser"})
    client.get_leagues = AsyncMock(return_value=[
        {"league_id": "L1", "name": "Test League", "season": "2025", "total_rosters": 10}
    ])
    client.get_nfl_state = AsyncMock(return_value={"season": "2025", "week": 1})
    return client


@pytest.mark.asyncio
async def test_lookup_returns_leagues(async_client):
    """LC-01: GET /sleeper/lookup returns leagues for valid username."""
    pytest.skip("Requires auth token from Wave 2 endpoints — implement in integration phase")


@pytest.mark.asyncio
async def test_bad_username_returns_404(async_client):
    """LC-08: Bad Sleeper username returns 404 with specific human-readable detail."""
    pytest.skip("Requires auth token from Wave 2 endpoints — implement in integration phase")
