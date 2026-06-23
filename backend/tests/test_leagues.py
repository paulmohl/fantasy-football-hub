"""Tests for LC-09 (ownership), LC-10 (dedup), LC-11 (disconnect)."""
import pytest


@pytest.mark.asyncio
async def test_ownership_returns_404_for_other_user(async_client):
    """LC-09: User cannot access another user's league."""
    pytest.skip("Requires league endpoints from Wave 3 Plan H")


@pytest.mark.asyncio
async def test_two_users_same_league_deduped(async_client):
    """LC-10: Two imports of same Sleeper league produce one league row."""
    pytest.skip("Requires league endpoints from Wave 3 Plan H")


@pytest.mark.asyncio
async def test_disconnect_removes_member_not_league(async_client):
    """LC-11: Disconnect deletes league_members row; league row remains."""
    pytest.skip("Requires league endpoints from Wave 3 Plan H")
