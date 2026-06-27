"""TradeEvaluator: head-to-head player comparison using FantasyCalc values (TM-08).

Pure functions — inputs come from ProjectionService.build_sleeper_id_index().
No I/O, no async.

Factors analyzed (from PATTERNS.md):
  1. Tier gap (maybeTier difference)
  2. trend30Day (value trajectory)
  3. injury_status (availability risk)
  4. Positional need context (passed in by caller)
"""
from __future__ import annotations


def compare_players(
    player_id_a: str,
    player_id_b: str,
    fc_index: dict[str, dict],
    player_lookup: dict[str, dict],
    team_needs: list[str] | None = None,
) -> dict:
    """Compare two players head-to-head; return recommendation, delta, confidence, factors.

    Args:
        player_id_a: Sleeper player_id of first player.
        player_id_b: Sleeper player_id of second player.
        fc_index: FantasyCalc index from build_sleeper_id_index().
        player_lookup: Full Sleeper player dict.
        team_needs: Positions the user's team needs (for positional need factor).

    Returns:
        {winner, loser, value_delta, confidence, factors (list of 3), recommendation (str)}
    """
    fc_a = fc_index.get(player_id_a)
    fc_b = fc_index.get(player_id_b)
    player_a = player_lookup.get(player_id_a, {})
    player_b = player_lookup.get(player_id_b, {})

    val_a = fc_a["value"] if fc_a else 0
    val_b = fc_b["value"] if fc_b else 0
    value_delta = val_a - val_b
    winner = player_id_a if value_delta >= 0 else player_id_b
    loser = player_id_b if value_delta >= 0 else player_id_a

    name_a = player_a.get("full_name", "Player A")
    name_b = player_b.get("full_name", "Player B")
    winner_name = name_a if winner == player_id_a else name_b
    loser_name = name_b if winner == player_id_a else name_a

    # Confidence: based on gap size relative to scale
    gap_pct = abs(value_delta) / 11000
    confidence = min(100, max(10, round(gap_pct * 100 * 3)))

    # Factor 1: Tier comparison
    tier_a = (fc_a or {}).get("maybeTier") or 99
    tier_b = (fc_b or {}).get("maybeTier") or 99
    factors = [{
        "label": "Trade value tier",
        "detail": (
            f"{winner_name} is in tier {min(tier_a, tier_b)} vs {loser_name} tier {max(tier_a, tier_b)}"
            if tier_a != tier_b
            else "Both players in the same tier"
        ),
    }]

    # Factor 2: 30-day trend
    trend_a = (fc_a or {}).get("trend30Day", 0)
    trend_b = (fc_b or {}).get("trend30Day", 0)
    trend_winner = trend_a if winner == player_id_a else trend_b
    trend_loser = trend_b if winner == player_id_a else trend_a
    if abs(trend_winner - trend_loser) > 50:
        trend_desc = "rising" if trend_winner > 0 else "falling"
        factors.append({
            "label": "30-day value trend",
            "detail": (
                f"{winner_name} value is {trend_desc} "
                f"({'+' if trend_winner > 0 else ''}{trend_winner}) vs "
                f"{loser_name} ({'+' if trend_loser > 0 else ''}{trend_loser})"
            ),
        })
    else:
        factors.append({
            "label": "30-day value trend",
            "detail": "Similar trajectory for both players over the past 30 days",
        })

    # Factor 3: Injury risk or positional need or rostered %
    inj_a = player_a.get("injury_status")
    inj_b = player_b.get("injury_status")
    pos_a = (player_a.get("fantasy_positions") or ["?"])[0]
    pos_b = (player_b.get("fantasy_positions") or ["?"])[0]
    needs = set(team_needs or [])

    if inj_a or inj_b:
        winner_inj = inj_a if winner == player_id_a else inj_b
        loser_inj = inj_b if winner == player_id_a else inj_a
        factors.append({
            "label": "Injury status",
            "detail": (
                f"{winner_name}: {winner_inj or 'Active'} | {loser_name}: {loser_inj or 'Active'}"
            ),
        })
    elif pos_a in needs or pos_b in needs:
        needed = pos_a if pos_a in needs else pos_b
        factors.append({
            "label": "Positional need",
            "detail": f"Your team has a positional need at {needed}",
        })
    else:
        roster_pct_a = (fc_a or {}).get("maybeRosterPercent", 0) or 0
        roster_pct_b = (fc_b or {}).get("maybeRosterPercent", 0) or 0
        factors.append({
            "label": "League rostered %",
            "detail": (
                f"{winner_name} rostered in {round(roster_pct_a * 100)}% of leagues "
                f"vs {round(roster_pct_b * 100)}%"
            ),
        })

    trend_direction = "rising" if (trend_a if winner == player_id_a else trend_b) > 0 else "falling"
    recommendation = (
        f"Start {winner_name} — {round(abs(value_delta) / 11000 * 100, 1)}% higher trade value"
        + (
            f" with a {trend_direction} trend."
            if abs(trend_winner - trend_loser) > 50
            else "."
        )
    )

    return {
        "winner": winner,
        "loser": loser,
        "value_delta": value_delta,
        "confidence": confidence,
        "factors": factors[:3],
        "recommendation": recommendation,
    }
