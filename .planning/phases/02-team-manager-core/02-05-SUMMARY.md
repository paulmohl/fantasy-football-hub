---
phase: 02-team-manager-core
plan: "05"
subsystem: backend-waiver-trade-services
tags: [waiver-ranker, trade-evaluator, dual-mode-scoring, pure-function, tdd, fantasycalc]
dependency_graph:
  requires:
    - backend/tests/fixtures/fc_values_sample.json (from Plan 01 — 20 sample FC entries)
    - backend/tests/fixtures/sleeper_players_sample.json (from Plan 01 — 25 sample players)
    - backend/tests/test_waiver_ranker.py (from Plan 01 — 4 test stubs)
    - backend/app/services/lineup_optimizer.py (Plan 04 — WONT_PLAY_STATUS reference)
  provides:
    - backend/app/services/waiver_ranker.py (score_waiver_player, rank_waiver_wire, suggest_drop_candidates, detect_waiver_type, recommend_faab_bid)
    - backend/app/services/trade_evaluator.py (compare_players)
  affects:
    - team.py router (Wave 3) — calls rank_waiver_wire for GET /team/waiver and compare_players for GET /team/trade
tech_stack:
  added: []
  patterns:
    - Pure function modules (no class, no I/O, no async)
    - Dual-mode scoring (trend-weighted + composite returned simultaneously for frontend toggle)
    - Injury multiplier lookup table for both modes
    - FantasyCalc value normalization to 0-1 scale for composite scoring
    - FAAB bid formula: percentile-based with positional scarcity factor and trend confidence range
key_files:
  created:
    - backend/app/services/waiver_ranker.py
    - backend/app/services/trade_evaluator.py
  modified: []
decisions:
  - Both trend_score and composite_score computed per player; frontend toggles display (DECISION-003)
  - fc_index keyed by sleeperId with value at top level (matches test fixture structure)
  - compare_players always returns exactly 3 factors (tier, trend, then injury/positional/roster% by priority)
  - Confidence in TradeEvaluator capped 10-100 (never 0 — avoids "no signal" UX)
  - winner uses >= not > so ties go to player_id_a (consistent tiebreak)
metrics:
  duration: "~5 minutes"
  completed: "2026-06-27T11:13:40Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 02 Plan 05: WaiverRanker + TradeEvaluator Summary

**One-liner:** Dual-mode waiver scoring (trend-weighted + composite) with FAAB bid recommendation, drop candidate ranking, and head-to-head player trade comparison via FantasyCalc values.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement WaiverRanker (dual-mode scoring) | 3922dd9 | waiver_ranker.py |
| 2 | Implement TradeEvaluator (player comparison) | 73ad909 | trade_evaluator.py |

## What Was Built

### waiver_ranker.py — Pure Function Module

**Exports:**
- `score_waiver_player(player_id, trending_count, fc_value, recent_pts, season_avg_pts, team_needs, player_position, injury_status) -> dict`
  - Returns `{player_id, trend_score, composite_score}`
  - Trend-weighted: `(recent_pts * 0.7 + season_avg_pts * 0.3) * (1 + trending_count/100) * inj_mult * need_bonus`
  - Composite: 35% FC value + 35% trend normalized + 15% trending count + 15% injury multiplier, scaled 0-100+

- `rank_waiver_wire(...) -> list[dict]`
  - Filters out rostered_ids and invalid IDs ("0", "")
  - Returns all eligible players with both scores; sorted by composite_score descending
  - Frontend re-sorts by trend_score for trend mode

- `suggest_drop_candidates(rostered_ids, fc_index, in_progress_ids, locked_ids, ...) -> list[dict]`
  - Excludes in_progress_ids and locked_ids
  - Sorts by ros_value ascending (lowest value = best drop candidate)
  - Returns max 3 entries

- `detect_waiver_type(league_settings) -> "faab" | "rolling"`
  - `waiver_type == 2` → "faab"; any other value → "rolling"

- `recommend_faab_bid(player_id, fc_value, remaining_budget, positional_scarcity, trend30_day) -> dict`
  - `mid_bid = (fc_value / 11000) * remaining_budget * scarcity_factor`
  - `confidence_range = mid_bid * (0.15–0.30)` based on trend certainty
  - Returns `{mid_bid, confidence_range, min_bid, max_bid}`

**Injury multipliers:**
- Out/Suspended/IR/PUP/NA/DNR → 0.0 (excluded from composite)
- Doubtful → 0.4, Questionable → 0.8, Active → 1.0

### trade_evaluator.py — Pure Function Module

**Exports:**
- `compare_players(player_id_a, player_id_b, fc_index, player_lookup, team_needs=None) -> dict`
  - Returns `{winner, loser, value_delta, confidence, factors (list[3]), recommendation}`
  - Factor 1: Trade value tier (maybeTier comparison)
  - Factor 2: 30-day value trend (trend30Day; notes "rising"/"falling" when gap > 50)
  - Factor 3: Injury status (if either injured) → positional need (if team_needs match) → league rostered %
  - Confidence: `min(100, max(10, round(abs(value_delta) / 11000 * 100 * 3)))`

## Verification

```
pytest tests/test_waiver_ranker.py -v
4 passed, 5 warnings in 0.10s
```

Full suite: 55 passed, 7 skipped, 14 warnings — no regressions.

```
python -c "from app.services.trade_evaluator import compare_players; result = compare_players('x','y',{},{}); assert 'winner' in result; assert len(result['factors']) == 3; print('TradeEvaluator OK')"
TradeEvaluator OK
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — both modules return fully computed data. No placeholder values.

## Threat Flags

T-02-05-01: `suggest_drop_candidates` locked_ids is received from the caller (team.py router). This service layer correctly treats it as opaque — it only excludes entries in locked_ids, never modifies or validates them. Enforcement that locked_ids is computed server-side from roster rules is the router's responsibility (Wave 3).

## Self-Check: PASSED
