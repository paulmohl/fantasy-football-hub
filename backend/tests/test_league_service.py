"""Tests for yahoo_service (03-05) and espn_service (03-06).

Covers: normalization functions (pure unit tests), import functions (DB + mock clients).
"""
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.league import League, LeagueMember, Team
from app.models.user import User
from app.services.espn_client import ESPNAuthExpired
from app.services.espn_service import (
    import_espn_league,
    normalize_espn_roster_format,
    normalize_espn_scoring,
)
from app.services.yahoo_service import (
    import_yahoo_league,
    normalize_yahoo_roster_format,
    normalize_yahoo_scoring,
)

# ── Fixture builders ───────────────────────────────────────────────────────────

def _yahoo_settings(max_keepers: int = 3, keeper_cost_type: int = 1, extra_stats: list | None = None) -> dict:
    stats = {
        "0": {"stat": {"stat_id": 11, "value": 1.0}},   # rec = 1.0
        "1": {"stat": {"stat_id": 4, "value": 0.04}},   # pass_yd
        "2": {"stat": {"stat_id": 5, "value": 6.0}},    # pass_td
    }
    if extra_stats:
        for i, s in enumerate(extra_stats, start=len(stats)):
            stats[str(i)] = s
    return {
        "fantasy_content": {
            "league": [
                {"season": "2025", "name": "Test Yahoo League", "draft_type": "snake"},
                {
                    "settings": {
                        "max_keepers": max_keepers,
                        "keeper_cost_type": keeper_cost_type,
                        "stat_categories": {"stats": stats},
                        "roster_positions": {
                            "0": {"roster_position": {"position_type": "QB", "count": 1}},
                            "1": {"roster_position": {"position_type": "WR", "count": 2}},
                            "2": {"roster_position": {"position_type": "W/R/T", "count": 2}},
                            "3": {"roster_position": {"position_type": "Q/W/R/T", "count": 1}},
                            "4": {"roster_position": {"position_type": "W/T", "count": 1}},
                            "5": {"roster_position": {"position_type": "W/R", "count": 1}},
                            "6": {"roster_position": {"position_type": "BN", "count": 5}},
                        },
                    }
                },
            ]
        }
    }


def _yahoo_teams(team_id: str = "1", team_name: str = "Team Alpha") -> dict:
    return {
        "fantasy_content": {
            "league": [
                {},
                {
                    "teams": {
                        "0": {
                            "team": [
                                [{"team_id": team_id}, {"name": team_name}],
                                {},
                            ]
                        },
                        "count": 1,
                    }
                },
            ]
        }
    }


def _yahoo_roster(yahoo_player_id: str = "9876", position: str = "QB") -> dict:
    is_bench = position == "BN"
    return {
        "fantasy_content": {
            "team": [
                {},
                {
                    "roster": {
                        "0": {
                            "players": {
                                "0": {
                                    "player": [
                                        {"player_id": yahoo_player_id},
                                        {"selected_position": [{}, {"position": position}]},
                                    ]
                                }
                            }
                        }
                    }
                },
            ]
        }
    }


def _espn_league_data(
    name: str = "Test ESPN League",
    keeper_count: int = 0,
    keeper_order_type: int = 0,
    num_teams: int = 2,
    scoring_items: list | None = None,
    slot_counts: dict | None = None,
) -> dict:
    if scoring_items is None:
        scoring_items = [
            {"statId": 41, "points": 1.0},   # rec
            {"statId": 3, "points": 0.04},   # pass_yd
            {"statId": 4, "points": 4.0},    # pass_td
        ]
    if slot_counts is None:
        slot_counts = {"0": 1, "23": 2, "24": 5}

    teams = []
    for i in range(1, num_teams + 1):
        teams.append({
            "id": i,
            "location": "Team",
            "nickname": f"Team{i}",
            "roster": {
                "entries": [
                    {"playerId": 3000 + i, "lineupSlotId": 0},   # active QB
                    {"playerId": 4000 + i, "lineupSlotId": 24},  # bench
                ]
            },
        })
    return {
        "settings": {
            "name": name,
            "size": num_teams,
            "acquisitionSettings": {
                "keeperCount": keeper_count,
                "keeperOrderType": keeper_order_type,
            },
            "scoringSettings": {"scoringItems": scoring_items},
            "rosterSettings": {"lineupSlotCounts": slot_counts},
        },
        "teams": teams,
    }


def _mock_redis() -> MagicMock:
    r = MagicMock()
    r.set = AsyncMock(return_value=True)
    r.get = AsyncMock(return_value=None)
    return r


# ═══════════════════════════════════════════════════════════════════════════════
# YAHOO TESTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── normalize_yahoo_scoring ────────────────────────────────────────────────────

def test_normalize_yahoo_scoring_ppr():
    data = _yahoo_settings()
    result = normalize_yahoo_scoring(data)
    assert result["normalized"]["rec"] == 1.0
    assert "normalized" in result
    assert "platform_raw" in result


def test_normalize_yahoo_scoring_standard():
    data = _yahoo_settings()
    # Override rec to 0
    data["fantasy_content"]["league"][1]["settings"]["stat_categories"]["stats"]["0"]["stat"]["value"] = 0.0
    result = normalize_yahoo_scoring(data)
    assert "rec" not in result["normalized"]


def test_keeper_extraction():
    data = _yahoo_settings(max_keepers=3, keeper_cost_type=1)
    result = normalize_yahoo_scoring(data)
    ks = result["keeper_settings"]
    assert ks["max_keepers"] == 3
    assert ks["keeper_cost_type"] == 1


def test_unmodeled_rules():
    unknown_stat = {"stat": {"stat_id": 9999, "value": 2.0}}
    data = _yahoo_settings(extra_stats=[unknown_stat])
    result = normalize_yahoo_scoring(data)
    assert "yahoo_stat_9999" in result["keeper_settings"]["unmodeled_rules"]


def test_normalize_roster_flex():
    data = _yahoo_settings()
    result = normalize_yahoo_roster_format(data)
    assert "FLEX" in result["positions"]
    assert "SUPERFLEX" in result["positions"]


def test_normalize_roster_wr_rb_te():
    data = _yahoo_settings()
    result = normalize_yahoo_roster_format(data)
    positions = result["positions"]
    assert positions.count("FLEX") >= 4   # W/R/T x2 + W/T x1 + W/R x1
    assert "SUPERFLEX" in positions       # Q/W/R/T x1


# ── import_yahoo_league (DB tests) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_yahoo_league_keeper_flag(test_db):
    uid = uuid4()
    test_db.add(User(id=uid, email="yahoo1@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    settings_data = _yahoo_settings(max_keepers=3)
    yahoo = MagicMock()
    yahoo.get_league_settings = AsyncMock(return_value=settings_data)
    yahoo.get_league_teams = AsyncMock(return_value=_yahoo_teams())
    yahoo.get_team_roster = AsyncMock(return_value=_yahoo_roster())

    league = await import_yahoo_league("1234", "461", user, test_db, _mock_redis(), yahoo)
    assert league.keeper_flag is True
    assert league.host_platform == "yahoo"


@pytest.mark.asyncio
async def test_import_yahoo_league_data_completeness(test_db):
    uid = uuid4()
    test_db.add(User(id=uid, email="yahoo2@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    yahoo = MagicMock()
    yahoo.get_league_settings = AsyncMock(return_value=_yahoo_settings())
    yahoo.get_league_teams = AsyncMock(return_value=_yahoo_teams())
    yahoo.get_team_roster = AsyncMock(return_value=_yahoo_roster())

    league = await import_yahoo_league("5678", "461", user, test_db, _mock_redis(), yahoo)
    assert league.season == "2025"
    assert league.name == "Test Yahoo League"
    assert "normalized" in league.scoring_rules
    assert "positions" in league.roster_format


@pytest.mark.asyncio
async def test_yahoo_keeper_extraction(test_db):
    """MP-09: keeper settings extracted from Yahoo import."""
    uid = uuid4()
    test_db.add(User(id=uid, email="yahoo3@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    yahoo = MagicMock()
    yahoo.get_league_settings = AsyncMock(return_value=_yahoo_settings(max_keepers=5))
    yahoo.get_league_teams = AsyncMock(return_value=_yahoo_teams())
    yahoo.get_team_roster = AsyncMock(return_value=_yahoo_roster())

    league = await import_yahoo_league("9999", "461", user, test_db, _mock_redis(), yahoo)
    assert league.scoring_rules["keeper_settings"]["max_keepers"] == 5


@pytest.mark.asyncio
async def test_roster_snapshot_has_sleeper_id_yahoo(test_db):
    """Roster snapshot players list contains sleeper_id field (None when unmapped)."""
    from sqlalchemy import select as sa_select
    uid = uuid4()
    test_db.add(User(id=uid, email="yahoo4@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    yahoo = MagicMock()
    yahoo.get_league_settings = AsyncMock(return_value=_yahoo_settings())
    yahoo.get_league_teams = AsyncMock(return_value=_yahoo_teams())
    yahoo.get_team_roster = AsyncMock(return_value=_yahoo_roster(yahoo_player_id="1111", position="QB"))

    await import_yahoo_league("7777", "461", user, test_db, _mock_redis(), yahoo)

    from app.models.league import Roster, Team
    team_result = await test_db.execute(sa_select(Team))
    team = team_result.scalar_one()
    roster_result = await test_db.execute(sa_select(Roster).where(Roster.team_id == team.id))
    roster = roster_result.scalar_one()
    players = roster.snapshot["players"]
    assert len(players) == 1
    assert "sleeper_id" in players[0]
    assert "yahoo_id" in players[0]
    assert players[0]["yahoo_id"] == "1111"


# ═══════════════════════════════════════════════════════════════════════════════
# ESPN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── normalize_espn_scoring ─────────────────────────────────────────────────────

def test_normalize_espn_scoring_ppr():
    data = _espn_league_data()
    result = normalize_espn_scoring(data)
    assert result["normalized"]["rec"] == 1.0


def test_normalize_espn_scoring_unknown_stat():
    data = _espn_league_data(scoring_items=[{"statId": 9999, "points": 5.0}])
    result = normalize_espn_scoring(data)
    assert "espn_stat_9999" in result["keeper_settings"]["unmodeled_rules"]


def test_espn_keeper_extraction():
    data = _espn_league_data(keeper_count=3, keeper_order_type=1)
    result = normalize_espn_scoring(data)
    ks = result["keeper_settings"]
    assert ks["max_keepers"] == 3
    assert ks["keeper_cost_type"] == 1


def test_espn_roster_flex():
    data = _espn_league_data(slot_counts={"23": 2, "24": 5})
    result = normalize_espn_roster_format(data)
    assert result["positions"].count("FLEX") == 2


def test_espn_roster_superflex():
    data = _espn_league_data(slot_counts={"20": 1, "24": 5})
    result = normalize_espn_roster_format(data)
    assert "SUPERFLEX" in result["positions"]


# ── import_espn_league (DB tests) ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_espn_private_league(test_db):
    uid = uuid4()
    test_db.add(User(id=uid, email="espn1@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    espn = MagicMock()
    espn.get_league = AsyncMock(return_value=_espn_league_data(keeper_count=3))

    league = await import_espn_league("336541", 2025, False, user, test_db, _mock_redis(), espn)
    assert league.host_platform == "espn"
    assert league.keeper_flag is True


@pytest.mark.asyncio
async def test_import_espn_public_league(test_db):
    uid = uuid4()
    test_db.add(User(id=uid, email="espn2@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    espn = MagicMock()
    espn.get_league = AsyncMock(return_value=_espn_league_data())

    await import_espn_league("336541", 2025, True, user, test_db, _mock_redis(), espn)

    from sqlalchemy import select as sa_select
    member_result = await test_db.execute(
        sa_select(LeagueMember).where(LeagueMember.user_id == uid)
    )
    member = member_result.scalar_one()
    assert member.role == "viewer"


@pytest.mark.asyncio
async def test_espn_all_teams_parsed(test_db):
    """Pitfall 6: all 3 teams from ESPN response["teams"] must be persisted."""
    uid = uuid4()
    test_db.add(User(id=uid, email="espn3@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    espn = MagicMock()
    espn.get_league = AsyncMock(return_value=_espn_league_data(num_teams=3))

    from sqlalchemy import select as sa_select
    league = await import_espn_league("336541", 2025, False, user, test_db, _mock_redis(), espn)

    team_result = await test_db.execute(sa_select(Team).where(Team.league_id == league.id))
    teams = team_result.scalars().all()
    assert len(teams) == 3


@pytest.mark.asyncio
async def test_no_partial_write_on_error(test_db):
    """ESPNAuthExpired raised before DB opened → no League row created."""
    uid = uuid4()
    test_db.add(User(id=uid, email="espn4@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    espn = MagicMock()
    espn.get_league = AsyncMock(side_effect=ESPNAuthExpired("expired"))

    with pytest.raises(ESPNAuthExpired):
        await import_espn_league("bad_league", 2025, False, user, test_db, _mock_redis(), espn)

    from sqlalchemy import select as sa_select
    league_result = await test_db.execute(sa_select(League).where(League.host_platform == "espn"))
    assert league_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_roster_snapshot_has_sleeper_id_espn(test_db):
    from sqlalchemy import select as sa_select
    uid = uuid4()
    test_db.add(User(id=uid, email="espn5@test.com", password_hash=None, is_verified=False))
    await test_db.flush()
    user = (await test_db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(User).where(User.id == uid)
    )).scalar_one()

    espn = MagicMock()
    espn.get_league = AsyncMock(return_value=_espn_league_data(num_teams=1))

    await import_espn_league("99999", 2025, False, user, test_db, _mock_redis(), espn)

    from app.models.league import Roster, Team
    team_result = await test_db.execute(sa_select(Team))
    team = team_result.scalar_one()
    roster_result = await test_db.execute(sa_select(Roster).where(Roster.team_id == team.id))
    roster = roster_result.scalar_one()
    players = roster.snapshot["players"]
    assert len(players) == 2
    assert "sleeper_id" in players[0]
    assert "espn_id" in players[0]
