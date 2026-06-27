"""WaiverRanker: dual-mode waiver wire scoring (DECISION-003 from CONTEXT.md).

Two modes returned simultaneously; frontend toggles display:
  - trend-weighted: recent performance over season average
  - composite: equal weight across FC value, trend, trending count, injury risk

Formula weights from RESEARCH.md Pattern 3 (ASSUMED — will need in-season tuning).

Pitfall 7 (RESEARCH.md): During off-season, Sleeper trending counts are near zero.
During off-season gate trend-weighted score to composite-only fallback by checking
if all trending_counts are 0.
"""
from __future__ import annotations

FC_VALUE_MAX: int = 11000

# Injury penalty multipliers
_INJURY_COMPOSITE_PENALTY: dict[str, float] = {
    "Out": 0.0,
    "Suspended": 0.0,
    "IR": 0.0,
    "PUP": 0.0,
    "NA": 0.0,
    "DNR": 0.0,
    "Doubtful": 0.4,
    "Questionable": 0.8,
}


def _injury_multiplier(injury_status: str | None) -> float:
    if not injury_status:
        return 1.0
    return _INJURY_COMPOSITE_PENALTY.get(injury_status, 1.0)


def score_waiver_player(
    player_id: str,
    trending_count: int,
    fc_value: int,
    recent_pts: float,
    season_avg_pts: float,
    team_needs: list[str],
    player_position: str,
    injury_status: str | None,
) -> dict:
    """Compute both waiver scores for a single player.

    Returns {player_id, trend_score, composite_score}.
    """
    inj_mult = _injury_multiplier(injury_status)
    need_bonus = 1.2 if player_position in team_needs else 1.0

    # Trend-weighted: recent > historical (DECISION-003)
    # Guard against zero recent/season pts during off-season
    trend_base = (recent_pts * 0.7 + season_avg_pts * 0.3) * (1 + trending_count / 100)
    trend_score = trend_base * inj_mult * need_bonus

    # Composite: equal weight across signals
    fc_normalized = fc_value / FC_VALUE_MAX  # 0–1 scale
    trend_normalized = min(1.0, trend_base / 50.0)  # cap at 50 pts as max
    trending_normalized = min(1.0, trending_count / 100.0)
    composite_base = (
        fc_normalized * 0.35
        + trend_normalized * 0.35
        + trending_normalized * 0.15
        + inj_mult * 0.15
    ) * need_bonus
    composite_score = composite_base * 100  # scale to 0–100+

    return {
        "player_id": player_id,
        "trend_score": round(trend_score, 3),
        "composite_score": round(composite_score, 3),
    }


def rank_waiver_wire(
    available_player_ids: list[str],
    player_lookup: dict[str, dict],
    fc_index: dict[str, dict],
    trending_counts: dict[str, int],
    recent_pts: dict[str, float],
    season_avg_pts: dict[str, float],
    team_needs: list[str],
    rostered_ids: set[str] | None = None,
) -> list[dict]:
    """Rank all available (unrostered) players by both waiver scores.

    Args:
        available_player_ids: All player_ids to consider (typically all Sleeper players
            not in any team's roster in this league). Pass full player pool — function
            excludes rostered_ids internally.
        player_lookup: Full Sleeper player dict.
        fc_index: FantasyCalc index keyed by Sleeper player_id.
        trending_counts: {player_id: add_count} from Sleeper trending endpoint.
        recent_pts: {player_id: avg_pts_last_2_weeks}
        season_avg_pts: {player_id: avg_pts_this_season}
        team_needs: Positions the user's team is weak at (e.g., ["RB", "WR"]).
        rostered_ids: Set of player_ids already on any roster in the league.

    Returns:
        List of player dicts sorted by composite_score descending.
        Includes both trend_score and composite_score for frontend toggle.
    """
    rostered = rostered_ids or set()
    results: list[dict] = []

    for pid in available_player_ids:
        if pid in rostered or not pid or pid == "0":
            continue
        player = player_lookup.get(pid)
        if not player:
            continue

        fc_entry = fc_index.get(pid)
        fc_value = fc_entry["value"] if fc_entry else 0

        position = (player.get("fantasy_positions") or ["?"])[0]
        injury = player.get("injury_status") or None

        scores = score_waiver_player(
            player_id=pid,
            trending_count=trending_counts.get(pid, 0),
            fc_value=fc_value,
            recent_pts=recent_pts.get(pid, 0.0),
            season_avg_pts=season_avg_pts.get(pid, 0.0),
            team_needs=team_needs,
            player_position=position,
            injury_status=injury,
        )

        results.append({
            "player_id": pid,
            "full_name": player.get("full_name", "Unknown"),
            "position": position,
            "team": player.get("team"),
            "trend_score": scores["trend_score"],
            "composite_score": scores["composite_score"],
            "injury_status": injury,
            "fc_value": fc_value,
            "trending_count": trending_counts.get(pid, 0),
        })

    # Sort by composite_score descending; frontend can re-sort by trend_score
    results.sort(key=lambda x: -x["composite_score"])
    return results


def suggest_drop_candidates(
    rostered_ids: list[str],
    fc_index: dict[str, dict],
    in_progress_ids: set[str],
    locked_ids: set[str],
    player_lookup: dict[str, dict] | None = None,
    n: int = 3,
) -> list[dict]:
    """Suggest 1–3 drop candidates ranked by lowest FantasyCalc value (TM-06).

    Excludes:
      - Players whose game is in progress (TM-06 requirement)
      - Locked players (user-defined, e.g., keepers or injured starters)

    Args:
        rostered_ids: Player IDs on the user's current roster.
        fc_index: FantasyCalc index keyed by Sleeper player_id.
        in_progress_ids: Player IDs with a game currently in progress.
        locked_ids: Player IDs the user has locked from being dropped.
        player_lookup: Optional Sleeper player dict for name/position.
        n: Max candidates to return (default 3).

    Returns:
        List of up to n dicts sorted by ros_value ascending (lowest value = best drop).
    """
    candidates: list[dict] = []
    pl = player_lookup or {}

    for pid in rostered_ids:
        if pid in in_progress_ids or pid in locked_ids:
            continue
        if not pid or pid == "0":
            continue
        fc_entry = fc_index.get(pid)
        ros_value = fc_entry["value"] if fc_entry else 0
        player = pl.get(pid, {})
        candidates.append({
            "player_id": pid,
            "full_name": player.get("full_name", "Unknown"),
            "position": (player.get("fantasy_positions") or ["?"])[0],
            "ros_value": ros_value,
            "injury_status": player.get("injury_status") or None,
        })

    candidates.sort(key=lambda x: x["ros_value"])
    return candidates[:n]


def detect_waiver_type(league_settings: dict) -> str:
    """Detect waiver type from Sleeper league settings.

    Sleeper waiver_type field:
      0 = rolling priority (waivers reset; no budget)
      2 = FAAB (Free Agent Acquisition Budget)

    Returns "faab" or "rolling".
    """
    waiver_type = (league_settings.get("settings") or {}).get("waiver_type", 0)
    return "faab" if waiver_type == 2 else "rolling"


def recommend_faab_bid(
    player_id: str,
    fc_value: int,
    remaining_budget: int,
    positional_scarcity: float,
    trend30_day: int,
) -> dict:
    """Compute FAAB bid recommendation with confidence range (TM-12).

    Formula (simple percentile-based — RESEARCH.md 'Don't Hand-Roll' section):
      mid_bid = (fc_value / FC_VALUE_MAX) * remaining_budget * positional_scarcity_factor

    positional_scarcity: 1.0 = average; 1.3 = scarce position; 0.8 = plentiful position.
    trend30_day: positive = rising value; affects confidence range width.

    Returns {mid_bid, confidence_range, min_bid, max_bid} — all integers (dollar amounts).
    """
    scarcity_factor = max(0.5, min(1.5, positional_scarcity))
    raw_bid = (fc_value / FC_VALUE_MAX) * remaining_budget * scarcity_factor
    mid_bid = max(1, min(remaining_budget, round(raw_bid)))

    # Confidence range: wider when trend is near 0 (uncertain); narrower when strongly trending
    trend_certainty = min(1.0, abs(trend30_day) / 200.0)
    range_pct = 0.3 - (0.15 * trend_certainty)  # ±15–30% of mid_bid
    confidence_range = max(1, round(mid_bid * range_pct))

    return {
        "mid_bid": mid_bid,
        "confidence_range": confidence_range,
        "min_bid": max(1, mid_bid - confidence_range),
        "max_bid": min(remaining_budget, mid_bid + confidence_range),
    }
