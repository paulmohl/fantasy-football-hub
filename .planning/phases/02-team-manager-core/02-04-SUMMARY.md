---
phase: 02-team-manager-core
plan: "04"
subsystem: backend-lineup-optimizer
tags: [lineup-optimizer, greedy-algorithm, pure-function, injury-status, confidence-score, tdd]
dependency_graph:
  requires:
    - backend/tests/fixtures/fc_values_sample.json (from Plan 01 — 20 sample FC entries)
    - backend/tests/fixtures/sleeper_players_sample.json (from Plan 01 — 25 sample players)
    - backend/app/services/projection_service.py (from Plan 02 — build_sleeper_id_index output shape)
  provides:
    - backend/app/services/lineup_optimizer.py (build_optimal_lineup, WONT_PLAY_STATUS, INJURY_SEVERITY)
  affects:
    - team.py router (Wave 3) — calls build_optimal_lineup with roster snapshot + FC index
    - WaiverRanker (Wave 2) — shares WONT_PLAY_STATUS constants
tech_stack:
  added: []
  patterns:
    - Pure function module (no class, no I/O, no async)
    - Greedy descent slot assignment (O(n) — sufficient for standard roster slot counts)
    - frozenset membership test for injury status classification
    - FantasyCalc value normalization to 0-100 confidence scale
    - Sleeper search_rank proxy for players not in FC top-200
key_files:
  created:
    - backend/app/services/lineup_optimizer.py
  modified: []
decisions:
  - build_optimal_lineup returns list[dict] (not tuple) to match test iteration contract
  - Bench slots labeled "BN" (not "BN1"/"BN2") to match test filter s["slot"] not in ("BN", "IR")
  - Search_rank proxy: max(0, FC_VALUE_MAX - rank * 20) — gives Sleeper-only players a rough value estimate
  - Confidence formula: min(100, int(score / FC_VALUE_MAX * 100)) with -30 penalty for Doubtful
  - OUT players sorted last (score = -1.0) and placed in BN slots, never starters
  - replacement_suggestion searches BN entries for matching position on OUT player
metrics:
  duration: "~3 minutes"
  completed: "2026-06-27T11:09:00Z"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 02 Plan 04: LineupOptimizer Summary

**One-liner:** Greedy O(n) lineup slot assignment with FantasyCalc value normalization, injury-based confidence (0-100), OUT player exclusion, and bench replacement suggestions.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (GREEN) | Implement build_optimal_lineup (greedy slot assignment) | 402b269 | lineup_optimizer.py |

## What Was Built

### lineup_optimizer.py — Pure Function Module

**Exports:**
- `WONT_PLAY_STATUS: frozenset[str]` — `{"Out", "Suspended", "IR", "PUP", "NA", "DNR"}` (verified: support.sleeper.com)
- `INJURY_SEVERITY: dict[str | None, int]` — maps all Sleeper injury_status values to 0-4 severity scale
- `build_optimal_lineup(roster_player_ids, player_lookup, fc_index, roster_positions, current_starters=None) -> list[dict]`

**Algorithm (greedy descent):**
1. Filter empty Sleeper slot IDs (`"0"` and `""`) from roster
2. Score every player: FantasyCalc value (if in index) or `max(0, 11000 - search_rank * 20)` proxy
3. OUT/IR/Suspended/PUP/NA/DNR players get score = -1.0 (sorts last, never fills starter slots)
4. Sort descending by score
5. Fill starter slots (QB, RB×N, WR×N, TE, FLEX) in order with best eligible player
6. Remaining players fill BN slots; OUT players appended to BN after with `is_out=True`

**Confidence (0-100):**
- `min(100, int(score / 11000 * 100))`
- WONT_PLAY_STATUS → always 0
- Doubtful → subtract 30 from confidence (via halved score)

**FLEX slot:** accepts any player with `"RB"`, `"WR"`, or `"TE"` in `fantasy_positions`

**`replacement_suggestion`:** For each OUT player, finds the first BN entry whose player matches the OUT player's position.

**`is_swap_suggested`:** True when the optimal player for a slot differs from the corresponding `current_starters` entry.

**Slot labeling:**
- Single-occurrence slots: `"QB"`, `"TE"`, `"FLEX"`
- Multi-occurrence slots: first occurrence `"RB"`, second `"RB2"`, etc. (first has no suffix)
- Bench slots: `"BN"` (all bench entries share this label — test filter `slot not in ("BN", "IR")` is the contract)

## Verification

```
pytest tests/test_lineup_optimizer.py -v
4 passed, 5 warnings in 0.11s
```

Full suite: 51 passed, 11 skipped, 14 warnings — no regressions.

```
python -c "from app.services.lineup_optimizer import build_optimal_lineup, WONT_PLAY_STATUS; assert 'Out' in WONT_PLAY_STATUS; assert 'IR' in WONT_PLAY_STATUS; print('OK')"
OK
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Return type changed from tuple to list to match test iteration contract**
- **Found during:** Task 1 GREEN — first test run
- **Issue:** Plan's interface spec showed `Returns: (slot_assignments, metadata)` as a tuple, but the test code iterates directly over `result` (`for s in result if s["slot"] ...`). Iterating over a tuple yields the two tuple elements (list and dict), not the slot dicts.
- **Fix:** Changed return type to `list[dict]`. The `metadata` fields (`total_projected_points`, `no_strong_call`) are computable by callers from the slot list; the team.py router will compute them at call time.
- **Files modified:** `backend/app/services/lineup_optimizer.py`
- **Commit:** 402b269

**2. [Rule 1 - Bug] Bench slot labels changed from "BN1"/"BN2" to "BN"**
- **Found during:** Task 1 GREEN — `test_optimal_lineup_assigns_starters` got 10 starters instead of 7
- **Issue:** Tests filter starters with `s["slot"] not in ("BN", "IR")` using exact equality. Bench slots labeled `"BN1"`, `"BN2"` do not match `"BN"`, so all entries passed the filter yielding 10 instead of 7.
- **Fix:** Changed bench slot labels to `"BN"` (all bench entries share the same label). Internal bench distinction is not needed by the test contract.
- **Files modified:** `backend/app/services/lineup_optimizer.py`
- **Commit:** 402b269 (same commit — caught and fixed before commit)

## TDD Gate Compliance

| Gate | State | Status |
|------|-------|--------|
| RED | Wave 0 stubs used pytest.importorskip — 4 tests SKIPPED before lineup_optimizer.py existed | PASSED |
| GREEN | 402b269 — 4 tests PASSED after implementation | PASSED |

## Known Stubs

None — all implemented functionality is wired to real logic. No placeholder return values.

## Threat Flags

None — T-02-04-01 and T-02-04-02 were both `accept` disposition (inputs from server-side DB; projected_points are approximate proxies, not sensitive data).

## Self-Check: PASSED
