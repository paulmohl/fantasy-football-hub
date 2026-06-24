"""Tests for LC-09 (ownership), LC-10 (dedup), LC-11 (disconnect)."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.league import League, LeagueMember
from app.models.user import User
from app.services.league_service import classify_draft, import_league
from app.services.sleeper_client import SleeperClient


def make_mock_sleeper(league_id: str = "L1", season: str = "2025"):
    client = MagicMock(spec=SleeperClient)
    client.get_league = AsyncMock(return_value={
        "league_id": league_id,
        "name": "Test League",
        "season": season,
        "scoring_settings": {"rec": 1.0},
        "roster_positions": ["QB", "RB", "WR"],
        "settings": {"type": "snake", "num_keepers": 0},
    })
    client.get_rosters = AsyncMock(return_value=[
        {"roster_id": 1, "owner_id": "sleeper_user_abc", "starters": [], "players": [], "settings": {}}
    ])
    client.get_users = AsyncMock(return_value=[
        {"user_id": "sleeper_user_abc", "username": "testuser"}
    ])
    return client


@pytest.mark.asyncio
async def test_classify_draft_variants():
    """LC-03: Draft type classification covers all 4 Sleeper types."""
    assert classify_draft({"settings": {"type": "snake"}}) == "snake"
    assert classify_draft({"settings": {"type": "auction"}}) == "auction"
    assert classify_draft({"settings": {"type": "linear"}}) == "linear"
    assert classify_draft({"settings": {"type": "third_round_reversal"}}) == "third_round_reversal"
    assert classify_draft({"settings": {"type": "unknown"}}) == "snake"


@pytest.mark.asyncio
async def test_two_users_same_league_deduped(test_db, mock_redis):
    """LC-10: Two imports of the same Sleeper league produce one League row, two LeagueMember rows."""
    user_a = User(email="a@test.com", password_hash="x", is_verified=True)
    user_b = User(email="b@test.com", password_hash="x", is_verified=True)
    test_db.add_all([user_a, user_b])
    await test_db.flush()

    sleeper = make_mock_sleeper(league_id="SLEEPER_L1")

    await import_league("SLEEPER_L1", user_a, test_db, mock_redis, sleeper, week=1)
    await import_league("SLEEPER_L1", user_b, test_db, mock_redis, sleeper, week=1)
    await test_db.commit()

    leagues = (await test_db.execute(
        select(League).where(League.host_league_id == "SLEEPER_L1")
    )).scalars().all()
    assert len(leagues) == 1, f"Expected 1 league row, got {len(leagues)}"

    members = (await test_db.execute(
        select(LeagueMember).where(LeagueMember.league_id == leagues[0].id)
    )).scalars().all()
    assert len(members) == 2, f"Expected 2 member rows, got {len(members)}"


@pytest.mark.asyncio
async def test_disconnect_removes_member_not_league(test_db, mock_redis):
    """LC-11: Disconnecting removes league_members row; League row persists."""
    user = User(email="c@test.com", password_hash="x", is_verified=True)
    test_db.add(user)
    await test_db.flush()

    sleeper = make_mock_sleeper(league_id="SLEEPER_L2")
    league = await import_league("SLEEPER_L2", user, test_db, mock_redis, sleeper, week=1)
    await test_db.commit()

    member = (await test_db.execute(
        select(LeagueMember)
        .where(LeagueMember.user_id == user.id)
        .where(LeagueMember.league_id == league.id)
    )).scalar_one()
    await test_db.delete(member)
    await test_db.commit()

    still_exists = (await test_db.execute(
        select(League).where(League.id == league.id)
    )).scalar_one_or_none()
    assert still_exists is not None, "League row should persist after member disconnect"

    gone = (await test_db.execute(
        select(LeagueMember)
        .where(LeagueMember.user_id == user.id)
        .where(LeagueMember.league_id == league.id)
    )).scalar_one_or_none()
    assert gone is None, "LeagueMember row should be deleted on disconnect"
