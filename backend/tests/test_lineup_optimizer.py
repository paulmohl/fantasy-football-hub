"""Tests for LineupOptimizer (TM-01, TM-04).

Wave 0: stubs — all tests raise NotImplementedError until Wave 2 implements lineup_optimizer.py.
"""
import json
import os
import pytest
from unittest.mock import MagicMock


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str):
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def test_optimal_lineup_assigns_starters():
    """TM-01: Standard 1QB/2RB/2WR/1TE/1FLEX roster fills all 7 starter slots."""
    pytest.importorskip("app.services.lineup_optimizer")
    from app.services.lineup_optimizer import build_optimal_lineup
    fc_values = load_fixture("fc_values_sample.json")
    players = load_fixture("sleeper_players_sample.json")
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    roster_ids = list(players.keys())
    positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"]
    result = build_optimal_lineup(roster_ids, players, fc_index, positions)
    starters = [s for s in result if s["slot"] not in ("BN", "IR")]
    assert len(starters) == 7, f"Expected 7 starters, got {len(starters)}"
    for slot in starters:
        assert "confidence" in slot, "Each starter must have a confidence score"
        assert 0 <= slot["confidence"] <= 100, "Confidence must be 0–100"


def test_injured_player_excluded():
    """TM-01/TM-04: Player with injury_status='Out' is not placed in a starter slot."""
    pytest.importorskip("app.services.lineup_optimizer")
    from app.services.lineup_optimizer import build_optimal_lineup
    fc_values = load_fixture("fc_values_sample.json")
    players = load_fixture("sleeper_players_sample.json")
    # Mark top-ranked player as Out
    first_pid = list(players.keys())[0]
    players = dict(players)
    players[first_pid] = {**players[first_pid], "injury_status": "Out"}
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"]
    result = build_optimal_lineup(list(players.keys()), players, fc_index, positions)
    starter_ids = [s["player_id"] for s in result if s["slot"] not in ("BN", "IR")]
    assert first_pid not in starter_ids, "OUT player must not appear in starter slots"


def test_out_replacement():
    """TM-04: OUT player result includes a replacement_suggestion field."""
    pytest.importorskip("app.services.lineup_optimizer")
    from app.services.lineup_optimizer import build_optimal_lineup
    fc_values = load_fixture("fc_values_sample.json")
    players = load_fixture("sleeper_players_sample.json")
    first_pid = list(players.keys())[0]
    players = dict(players)
    players[first_pid] = {**players[first_pid], "injury_status": "Out"}
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"]
    result = build_optimal_lineup(list(players.keys()), players, fc_index, positions)
    out_entry = next((s for s in result if s["player_id"] == first_pid), None)
    assert out_entry is not None
    assert "replacement_suggestion" in out_entry, "OUT player must have replacement_suggestion"


def test_empty_slot_ids_filtered():
    """TM-01: Sleeper empty slot IDs ('0' and '') are ignored."""
    pytest.importorskip("app.services.lineup_optimizer")
    from app.services.lineup_optimizer import build_optimal_lineup
    fc_values = load_fixture("fc_values_sample.json")
    players = load_fixture("sleeper_players_sample.json")
    fc_index = {e["player"]["sleeperId"]: e for e in fc_values if e["player"].get("sleeperId")}
    roster_with_empties = ["0", "", *list(players.keys())[:10]]
    positions = ["QB", "RB", "WR", "FLEX", "BN", "BN", "BN"]
    result = build_optimal_lineup(roster_with_empties, players, fc_index, positions)
    result_ids = [s["player_id"] for s in result]
    assert "0" not in result_ids and "" not in result_ids, "Empty slot IDs must be filtered"
