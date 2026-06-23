"""Tests for LC-01 (Sleeper lookup) and LC-08 (error handling)."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_lookup_returns_leagues(async_client, mocker):
    """LC-01: GET /sleeper/lookup?username=X returns leagues list."""
    pytest.skip("Requires sleeper endpoints from Wave 3 Plan G")


@pytest.mark.asyncio
async def test_bad_username_returns_404(async_client, mocker):
    """LC-08: Bad Sleeper username returns 404 with detail."""
    pytest.skip("Requires sleeper endpoints from Wave 3 Plan G")
