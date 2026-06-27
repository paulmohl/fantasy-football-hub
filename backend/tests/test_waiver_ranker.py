"""Tests for WaiverRanker (TM-05, TM-06, TM-07).

Wave 0: stubs — all tests raise ImportError until Wave 2 implements waiver_ranker.py.
"""
import json
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def test_minimum_30_targets():
    """TM-05: WaiverRanker returns at least 30 targets from the full player pool."""
    pytest.importorskip("app.services.waiver_ranker")
    from app.services.waiver_ranker import rank_waiver_wire
    players = load_fixture("sleeper_players_sample.json")
    fc_values = load_fixture("fc_values_sample.json")
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    # All players available (empty rostered set)
    result = rank_waiver_wire(
        available_player_ids=list(players.keys()),
        player_lookup=players,
        fc_index=fc_index,
        trending_counts={},
        recent_pts={},
        season_avg_pts={},
        team_needs=["RB", "WR"],
    )
    assert len(result) >= min(30, len(players)), "Must return at least 30 targets (or all available)"


def test_trend_vs_composite():
    """TM-05: Trend-weighted score and composite score are both present and differ."""
    pytest.importorskip("app.services.waiver_ranker")
    from app.services.waiver_ranker import score_waiver_player
    result = score_waiver_player(
        player_id="1001",
        trending_count=50,
        fc_value=8000,
        recent_pts=25.0,
        season_avg_pts=18.0,
        team_needs=["RB"],
        player_position="RB",
        injury_status=None,
    )
    assert "trend_score" in result
    assert "composite_score" in result
    assert result["trend_score"] != result["composite_score"], "Scores should differ with unequal inputs"


def test_in_progress_player_excluded_from_drops():
    """TM-06: Players with game in progress excluded from drop candidates."""
    pytest.importorskip("app.services.waiver_ranker")
    from app.services.waiver_ranker import suggest_drop_candidates
    players = load_fixture("sleeper_players_sample.json")
    fc_values = load_fixture("fc_values_sample.json")
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    in_progress_ids = {list(players.keys())[0]}
    result = suggest_drop_candidates(
        rostered_ids=list(players.keys())[:10],
        fc_index=fc_index,
        in_progress_ids=in_progress_ids,
        locked_ids=set(),
    )
    assert all(r["player_id"] not in in_progress_ids for r in result), "In-progress players must be excluded"
    assert len(result) <= 3, "At most 3 drop candidates"


def test_waiver_type_detection():
    """TM-07: League with waiver_type=2 uses FAAB; waiver_type=0 uses rolling priority."""
    pytest.importorskip("app.services.waiver_ranker")
    from app.services.waiver_ranker import detect_waiver_type
    assert detect_waiver_type({"settings": {"waiver_type": 2}}) == "faab"
    assert detect_waiver_type({"settings": {"waiver_type": 0}}) == "rolling"
