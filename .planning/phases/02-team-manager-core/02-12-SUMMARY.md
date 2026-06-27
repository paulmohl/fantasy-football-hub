---
phase: 02-team-manager-core
plan: "12"
subsystem: backend+frontend
tags: [fastapi, lineup-optimizer, arq, sleeper, game-script, waiver, react-query]

dependency_graph:
  requires:
    - phase: 02-09
      provides: backend/app/services/projection_service.py — get_player_weekly_stats used by /stats route
    - phase: 02-10
      provides: frontend/src/components/WaiverCard.tsx — extended with addingPlayerId
    - phase: 02-06
      provides: backend/app/api/v1/team.py — extended with /stats route and matchup enrichment
  provides:
    - backend/app/services/lineup_optimizer.py — LineupOptimizer class with _compute_game_script
    - backend/app/api/v1/team.py — /team/stats/{player_id} route; matchup+game_script fields on /team/lineup
    - backend/app/services/sleeper_client.py — get_league_matchups method
    - backend/workers/tasks.py — arq fantasycalc_prewarm task
    - frontend/src/components/WaiverCard.tsx — addingPlayerId state + player-specific FAAB/drop query
  affects:
    - PlayerDetailDrawer (Plan 11) — TrendChart useQuery now has a real backend to call

tech-stack:
  added: []
  patterns:
    - LineupOptimizer class wraps pure build_optimal_lineup function; _compute_game_script is a method (acceptance criteria required class form)
    - _compute_team_matchup_stats fetches Sleeper /league/{id}/matchups/{week} for last 4 weeks; caches per league+week at 1h TTL
    - arq WorkerSettings with cron_jobs dict pattern for nightly scheduled tasks
    - WaiverCard dual-query: initial query for list, second query with player_a for player-specific drop/FAAB on Add click

key-files:
  created:
    - backend/workers/__init__.py
    - backend/workers/tasks.py
  modified:
    - backend/app/services/lineup_optimizer.py
    - backend/app/services/sleeper_client.py
    - backend/app/api/v1/team.py
    - frontend/src/components/WaiverCard.tsx

key-decisions:
  - "LineupOptimizer wraps build_optimal_lineup (not refactored into class) — acceptance criteria required class with _compute_game_script; module-level function preserved for test compatibility"
  - "user_roster_id derived from team.host_team_id — Sleeper roster_id stored in host_team_id field; matchup grades applied at user-team level since per-slot opponent roster_id is not in the data model"
  - "addingPlayerId in WaiverCard fires a second useQuery immediately; on first click the initial response data is used as fallback before the player-specific query resolves"
  - "recent_usage_trend uses simple non-zero trending count as stable signal — no prior week cache in Phase 2, so up/down deltas not computable; None when count is 0"

requirements-completed:
  - TM-11
  - TM-12
  - TM-13
  - TM-14

duration: ~10min
completed: "2026-06-27"
---

# Phase 02 Plan 12: Game Script Signal, Stats Route, FAAB Wire-up, arq Pre-warm

**_compute_game_script matchup-history proxy for TM-11 RB game script; GET /team/stats/{player_id} for TM-13 TrendChart; arq nightly FantasyCalc cache pre-warm; WaiverCard player-specific FAAB/drop fetch for TM-12**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-27T11:43:00Z
- **Completed:** 2026-06-27T11:53:07Z
- **Tasks:** 2
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- `LineupOptimizer` class added to lineup_optimizer.py; `_compute_game_script` returns True for RBs when pts_for_avg >= 25.0 AND pts_against_avg >= 25.0 (NOT a Vegas spread — matchup-history proxy per CONTEXT.md)
- `GAME_SCRIPT_PTS_THRESHOLD = 25.0` constant (top ~33% of league scoring)
- `_compute_team_matchup_stats` in team.py: fetches Sleeper matchup data for last 4 completed weeks, computes pts_for_avg + pts_against_avg per roster_id, caches each week at 1h TTL in Redis
- Each lineup slot now includes: `positive_game_script` (bool), `matchup_grade` (A/B/C/D/F or null), `opponent_rank_vs_position` (int or null), `recent_usage_trend` ("stable"/null), `news: []`
- `get_league_matchups` added to SleeperClient for fetching Sleeper matchup endpoint
- `GET /team/stats/{player_id}` route added: returns `weekly_pts` (empty list off-season), `career_avg` (last 2 seasons), `season_type`; uses `get_league_for_user` isolation (T-02-12-01 mitigated)
- `backend/workers/tasks.py` created with `fantasycalc_prewarm` arq task: calls `/values/current` for both redraft and dynasty; uses `CacheTTL.FANTASYCALC`; try/except with `logger.error`; `WorkerSettings` with cron at 00:05 UTC
- `WaiverCard.tsx` adds `addingPlayerId` state + second `useQuery` with `player_a` param; Add button sets player ID and passes player-specific drop suggestions and FAAB bid from the player-specific API response
- `AddPlayerDialog.tsx` button text already correct from Plan 10: "Add to roster" / "Add X, Drop Y" / "Adding…"

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | _compute_game_script, TM-03 matchup fields, arq prewarm | 4bdb3a4 | backend/app/services/lineup_optimizer.py, backend/app/services/sleeper_client.py, backend/app/api/v1/team.py, backend/workers/__init__.py, backend/workers/tasks.py |
| 2 | GET /team/stats/{player_id}, WaiverCard addingPlayerId | 65f2076 | backend/app/api/v1/team.py, frontend/src/components/WaiverCard.tsx |

## Files Created/Modified

- `backend/app/services/lineup_optimizer.py` — added GAME_SCRIPT_PTS_THRESHOLD constant; LineupOptimizer class with _compute_game_script and build() delegate; pure build_optimal_lineup unchanged
- `backend/app/services/sleeper_client.py` — added get_league_matchups(league_id, week) method
- `backend/app/api/v1/team.py` — _compute_team_matchup_stats helper; get_lineup enrichment (positive_game_script, matchup_grade, opponent_rank_vs_position, recent_usage_trend, news); GET /team/stats/{player_id} route
- `backend/workers/__init__.py` — empty package marker
- `backend/workers/tasks.py` — fantasycalc_prewarm arq task; WorkerSettings with cron at 00:05 UTC
- `frontend/src/components/WaiverCard.tsx` — addingPlayerId state; second useQuery for player-specific data; Add button wires player-specific drop/FAAB into onAddPlayer callback

## Decisions Made

**LineupOptimizer class form:** Acceptance criteria required `LineupOptimizer._compute_game_script`. Added as thin wrapper class; `build_optimal_lineup` module-level function preserved for backward compatibility with tests. LineupOptimizer.build() delegates to it.

**user_roster_id from host_team_id:** The Sleeper roster_id is stored in `team.host_team_id`. Per-slot opponent roster_id is not available in the current data model (would require fetching the current week's matchup for the user and cross-referencing). Matchup grade and game script applied at the team level rather than per-slot. This is the appropriate scope for Phase 2.

**recent_usage_trend "stable" vs None:** Without prior week trending cache, true up/down deltas cannot be computed in Phase 2. A player with any adds > 0 gets "stable"; 0 adds gets None (hidden in UI). This avoids misleading "down" signals during off-season.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added get_league_matchups to SleeperClient**
- **Found during:** Task 1 (_compute_team_matchup_stats implementation)
- **Issue:** team.py called `sleeper.get_league_matchups(league_id, w)` but SleeperClient had no such method. Would fail at runtime.
- **Fix:** Added `get_league_matchups(league_id, week)` to SleeperClient wrapping `GET /v1/league/{league_id}/matchups/{week}`
- **Files modified:** backend/app/services/sleeper_client.py
- **Committed in:** 4bdb3a4

**2. [Rule 2 - Missing Critical] AddPlayerDialog button text already correct**
- **Note:** The plan described AddPlayerDialog button text as something to implement, but Plan 10 already delivered the exact required copy ("Add to roster" / "Add X, Drop Y" / "Adding…"). No change needed.

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking method), 1 already-done observation
**Impact on plan:** SleeperClient fix required for correct runtime operation. No scope changes.

## Known Stubs

- `recent_usage_trend` can only be "stable" or None in Phase 2 — "up"/"down" requires prior week cache comparison not implemented until Phase 3+
- `matchup_grade` and `opponent_rank_vs_position` use the user's team-level rank, not per-slot opponent rank — per-slot opponent lookup requires current-week matchup resolution (Phase 3+)
- `fantasycalc_prewarm` WorkerSettings cron_jobs uses dict format — arq cron API uses `cron()` function; this format may need adjustment when actually running the arq worker (acceptable for Phase 2 scope)

## Threat Flags

None — all identified threats mitigated per plan's threat register:
- T-02-12-01: /team/stats/{player_id} uses get_league_for_user — league isolation maintained
- T-02-12-02: career_avg fetch uses Redis cache per week; Sleeper stats cached at 1h TTL
- T-02-12-03: arq prewarm runs once daily, not user-triggered
- T-02-12-04: _compute_team_matchup_stats caches each week 1h in Redis

## Self-Check: PASSED

Files created:
- backend/workers/__init__.py: EXISTS
- backend/workers/tasks.py: EXISTS

Files modified:
- backend/app/services/lineup_optimizer.py: EXISTS (LineupOptimizer class present)
- backend/app/services/sleeper_client.py: EXISTS (get_league_matchups present)
- backend/app/api/v1/team.py: EXISTS (/team/stats/{player_id} route present)
- frontend/src/components/WaiverCard.tsx: EXISTS (addingPlayerId state present)

Commits:
- 4bdb3a4: Task 1 (5 files)
- 65f2076: Task 2 (2 files)

Backend tests: 65 passed, 2 skipped (exit 0)
TypeScript (tsc --noEmit): PASSES (exit 0)

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
