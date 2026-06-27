"""Lineup optimizer: greedy slot assignment for fantasy football rosters.

Pure functions — no I/O, no async. The team.py router calls these after fetching
player data from ProjectionService.

Algorithm: greedy descent
  1. Score all players (FantasyCalc value + injury penalty)
  2. Sort descending by score
  3. Fill specific slots (QB, RB, WR, TE) first with highest-value eligible players
  4. Fill FLEX slot with highest remaining RB/WR/TE
  5. Remaining players go to bench

Confidence score (0–100):
  Derived from FantasyCalc value normalized to the top-200 range (0–12000).
  OUT/IR/Suspended/PUP players are set to 0.
  Questionable/Doubtful players have confidence reduced by 30.
  No FantasyCalc entry → confidence = max(0, 50 - search_rank) proxy.

This is NOT a true LP/ILP solver. Greedy is O(n) and sufficient for standard
lineup slot counts (RESEARCH.md Architecture Patterns Pattern 2).
"""
from __future__ import annotations

# Injury status sets from RESEARCH.md (verified: support.sleeper.com)
WONT_PLAY_STATUS: frozenset[str] = frozenset({"Out", "Suspended", "IR", "PUP", "NA", "DNR"})
UNLIKELY_STATUS: frozenset[str] = frozenset({"Doubtful"})

# Slots where a FLEX-eligible position can play
FLEX_ELIGIBLE: frozenset[str] = frozenset({"RB", "WR", "TE"})

# Non-starter slot names
NON_STARTER_SLOTS: frozenset[str] = frozenset({"BN", "IR"})

# FC value range for normalization (top-200 redraft values observed ~10500 max)
FC_VALUE_MAX: int = 11000

# Exported for external callers and tests
INJURY_SEVERITY: dict[str | None, int] = {
    None: 0,
    "": 0,
    "Active": 0,
    "Questionable": 1,
    "Doubtful": 2,
    "Out": 3,
    "Suspended": 3,
    "IR": 4,
    "PUP": 4,
    "NA": 4,
    "DNR": 4,
}


def _score_player(player_id: str, player: dict, fc_entry: dict | None) -> float:
    """Compute raw sort score. Higher = better start candidate."""
    injury = player.get("injury_status") or ""
    if injury in WONT_PLAY_STATUS:
        return -1.0  # Ensure OUT players sort last

    base_value: float
    if fc_entry:
        base_value = float(fc_entry.get("value", 0))
    else:
        # Sleeper search_rank proxy: invert rank (lower rank = higher score)
        rank = player.get("search_rank") or 500
        base_value = max(0.0, float(FC_VALUE_MAX) - rank * 20)

    if injury in UNLIKELY_STATUS:
        base_value *= 0.5  # Doubtful: halve value

    return base_value


def _confidence(score: float, injury: str | None) -> int:
    """Derive 0–100 confidence from normalized FantasyCalc value and injury status."""
    if injury in WONT_PLAY_STATUS:
        return 0
    raw_confidence = min(100, int(score / FC_VALUE_MAX * 100))
    if injury in UNLIKELY_STATUS:
        raw_confidence = max(0, raw_confidence - 30)
    return raw_confidence


def build_optimal_lineup(
    roster_player_ids: list[str],
    player_lookup: dict[str, dict],
    fc_index: dict[str, dict],
    roster_positions: list[str],
    current_starters: list[str] | None = None,
) -> list[dict]:
    """Greedy slot assignment for a fantasy football roster.

    Args:
        roster_player_ids: All player IDs on the roster (including bench).
            Sleeper empty slots ("0", "") are filtered automatically.
        player_lookup: Sleeper player dict keyed by player_id.
        fc_index: FantasyCalc index keyed by Sleeper player_id (from build_sleeper_id_index).
        roster_positions: Ordered slot list from League.roster_format["positions"],
            e.g. ["QB","RB","RB","WR","WR","TE","FLEX","BN","BN","BN"].
        current_starters: Optional list of player_ids currently in starter slots
            (same order as roster_positions starter slots). Used to set is_swap_suggested.

    Returns:
        list of slot dicts (one per position in roster_positions). Each slot includes
        player assignment, confidence, injury status, is_out, and replacement_suggestion.
        Access metadata via the slot list; aggregate projected_points from non-BN slots.
    """
    # Filter Sleeper empty slot IDs (Pitfall 4 from RESEARCH.md)
    valid_ids = [pid for pid in roster_player_ids if pid and pid != "0"]

    # Score every player
    scored: list[dict] = []
    for pid in valid_ids:
        player = player_lookup.get(pid, {})
        fc_entry = fc_index.get(pid)
        injury = player.get("injury_status") or ""
        raw_score = _score_player(pid, player, fc_entry)
        confidence = _confidence(raw_score, injury)
        scored.append({
            "player_id": pid,
            "full_name": player.get("full_name", "Unknown"),
            "position": (player.get("fantasy_positions") or ["?"])[0],
            "all_positions": player.get("fantasy_positions") or [],
            "score": raw_score,
            "confidence": confidence,
            "injury_status": injury or None,
            "is_out": injury in WONT_PLAY_STATUS,
        })

    scored.sort(key=lambda x: -x["score"])

    # Separate starter slots from bench
    starter_slot_types = [p for p in roster_positions if p not in NON_STARTER_SLOTS]
    bench_slot_count = roster_positions.count("BN")

    available = list(scored)  # mutable working list
    assignments: list[dict] = []

    def pop_best_for_slot(slot_type: str, pool: list[dict]) -> dict | None:
        """Remove and return best available player eligible for this slot."""
        for i, p in enumerate(pool):
            if p["is_out"]:
                continue
            eligible_positions = p["all_positions"]
            if slot_type == "FLEX":
                if any(pos in FLEX_ELIGIBLE for pos in eligible_positions):
                    return pool.pop(i)
            elif slot_type in eligible_positions:
                return pool.pop(i)
        return None

    # Deduplicate slot types for labeling (RB → RB1, RB2)
    slot_counter: dict[str, int] = {}
    current_starter_ids = list(current_starters) if current_starters else []
    flex_candidates_confidence: list[int] = []

    for slot_type in starter_slot_types:
        slot_counter[slot_type] = slot_counter.get(slot_type, 0) + 1
        count = slot_counter[slot_type]
        # Single slots keep their name (QB, TE, FLEX); multi slots get numbered (RB1, RB2, WR1, WR2)
        slot_label = f"{slot_type}{count}" if count > 1 else slot_type

        player_slot = pop_best_for_slot(slot_type, available)
        current_pid = current_starter_ids.pop(0) if current_starter_ids else None

        if player_slot:
            if slot_type == "FLEX":
                flex_candidates_confidence.append(player_slot["confidence"])
            assignments.append({
                "slot": slot_label,
                "player_id": player_slot["player_id"],
                "full_name": player_slot["full_name"],
                "position": player_slot["position"],
                "projected_points": round(player_slot["score"] / FC_VALUE_MAX * 40, 1),
                "confidence": player_slot["confidence"],
                "injury_status": player_slot["injury_status"],
                "is_out": False,
                "replacement_suggestion": None,
                "is_swap_suggested": current_pid != player_slot["player_id"],
            })
        else:
            assignments.append({
                "slot": slot_label,
                "player_id": None,
                "full_name": None,
                "position": None,
                "projected_points": 0.0,
                "confidence": 0,
                "injury_status": None,
                "is_out": False,
                "replacement_suggestion": None,
                "is_swap_suggested": False,
            })

    # Add bench (remaining available players, excluding OUT players already tracked)
    bench_counter = 0
    out_players = [p for p in scored if p["is_out"]]

    for p in available:
        if bench_counter >= bench_slot_count:
            break
        bench_counter += 1
        assignments.append({
            "slot": "BN",
            "player_id": p["player_id"],
            "full_name": p["full_name"],
            "position": p["position"],
            "projected_points": round(p["score"] / FC_VALUE_MAX * 40, 1),
            "confidence": p["confidence"],
            "injury_status": p["injury_status"],
            "is_out": False,
            "replacement_suggestion": None,
            "is_swap_suggested": False,
        })

    # Handle OUT players: add to overflow bench slots and set replacement_suggestion
    for out_player in out_players:
        # Find best bench player at same position for replacement suggestion
        replacement = None
        for bench_entry in assignments:
            if (
                bench_entry["slot"] == "BN"
                and bench_entry["player_id"]
                and out_player["position"] in player_lookup.get(bench_entry["player_id"], {}).get("fantasy_positions", [])
            ):
                replacement = bench_entry["player_id"]
                break

        assignments.append({
            "slot": "BN",
            "player_id": out_player["player_id"],
            "full_name": out_player["full_name"],
            "position": out_player["position"],
            "projected_points": 0.0,
            "confidence": 0,
            "injury_status": out_player["injury_status"],
            "is_out": True,
            "replacement_suggestion": replacement,
            "is_swap_suggested": False,
        })

    return assignments
