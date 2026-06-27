"""Integration tests for /api/v1/team/* routes (TM-01, TM-05, TM-07, LC-09 isolation).

Wave 0: stubs — all tests skip until Wave 3 implements team.py router.
"""
import pytest


@pytest.mark.asyncio
async def test_get_my_team_returns_200(async_client):
    """Route: GET /team/my — returns 200 with team + league data for authenticated user."""
    if True:  # Wave 0 stub — remove this guard in Wave 3 after team.py is implemented
        pytest.skip("team.py router not yet implemented — Wave 3")


@pytest.mark.asyncio
async def test_get_lineup_returns_optimal(async_client):
    """Route: GET /team/lineup — returns optimal lineup with confidence scores."""
    pytest.skip("team.py router not yet implemented — Wave 3")


@pytest.mark.asyncio
async def test_get_waiver_returns_ranked_list(async_client):
    """Route: GET /team/waiver — returns list with trend_score and composite_score."""
    pytest.skip("team.py router not yet implemented — Wave 3")


@pytest.mark.asyncio
async def test_waiver_type_detection_in_response(async_client):
    """TM-07: FAAB league response includes faab_budget; rolling league includes waiver_order."""
    pytest.skip("team.py router not yet implemented — Wave 3")


@pytest.mark.asyncio
async def test_team_isolation(async_client):
    """LC-09 carryover: /team/lineup with another user's league_id returns 404."""
    pytest.skip("team.py router not yet implemented — Wave 3")
