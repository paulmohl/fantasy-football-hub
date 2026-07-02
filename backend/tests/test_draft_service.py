"""Wave 0 stub tests for DraftService functions (DR-01,DR-02,DR-03,DR-04,DR-08,DR-14,DR-15).

These tests import from app.services.draft_service which does not exist until plan 04-03.
They are marked xfail and become real tests when 04-03 completes.
"""
import pytest

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_snake_pick_to_slot():
    from app.services.draft_service import snake_pick_to_slot
    assert snake_pick_to_slot(1, 12) == (1, 0)    # round 1, slot 0
    assert snake_pick_to_slot(12, 12) == (1, 11)   # round 1, slot 11
    assert snake_pick_to_slot(13, 12) == (2, 11)   # round 2 snakes back: slot 11
    assert snake_pick_to_slot(24, 12) == (2, 0)    # round 2, slot 0
    assert snake_pick_to_slot(25, 12) == (3, 0)    # round 3 goes forward again

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_build_draft_ics():
    from datetime import datetime
    from app.services.draft_service import build_draft_ics
    ics_bytes = build_draft_ics(
        draft_name="Test Draft",
        scheduled_at=datetime(2026, 8, 1, 20, 0),
        timezone_str="America/New_York",
        num_teams=12,
        clock_seconds=90,
        num_rounds=15,
    )
    assert b"BEGIN:VCALENDAR" in ics_bytes
    assert b"Fantasy Draft: Test Draft" in ics_bytes
    assert b"VTIMEZONE" in ics_bytes

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_tier_boundaries():
    from app.services.draft_service import compute_tier_boundaries
    players = [
        {"overall_rank": 1}, {"overall_rank": 2}, {"overall_rank": 3},
        {"overall_rank": 20},  # gap of 17 > 15 = new tier
        {"overall_rank": 21}, {"overall_rank": 22},
    ]
    boundaries = compute_tier_boundaries(players)
    assert 3 in boundaries  # tier break at index 3 (after rank 3 → rank 20)

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_auto_draft_selection(mock_redis_streams):
    pytest.skip("async test — implement after 04-03 with async fixture")

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_positional_need_weighting():
    from app.services.draft_service import positional_need_bonus
    roster = ["QB"]   # 1 QB already (position string, not player ID)
    # roster_format: QB has 1 starter slot → 0 unfilled → 0 bonus
    bonus_qb = positional_need_bonus(roster, "QB", {"QB": {"slots": 1}})
    assert bonus_qb == 0.0
    # 0 RBs, 2 RB slots → 2 unfilled → 10.0 bonus
    bonus_rb = positional_need_bonus([], "RB", {"RB": {"slots": 2}})
    assert bonus_rb == 10.0

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_csv_rankings_import():
    pytest.skip("async db test — implement after 04-03")

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_redis_stream_replay():
    pytest.skip("async redis test — implement after 04-03")

@pytest.mark.xfail(strict=False, reason="stub: app.services.draft_service created in plan 04-03")
def test_adp_grade_computation():
    from app.services.draft_service import compute_adp_grades
    picks_by_team = {
        "team_a": [{"player_id": "p1", "pick_num": 1}, {"player_id": "p2", "pick_num": 2}],
        "team_b": [{"player_id": "p3", "pick_num": 3}, {"player_id": "p4", "pick_num": 4}],
    }
    adp_lookup = {"p1": 5.0, "p2": 10.0, "p3": 1.0, "p4": 2.0}
    grades = compute_adp_grades(picks_by_team, adp_lookup)
    assert set(grades.keys()) == {"team_a", "team_b"}
    assert grades["team_a"] in ("A+", "A", "B", "C", "D", "F")
