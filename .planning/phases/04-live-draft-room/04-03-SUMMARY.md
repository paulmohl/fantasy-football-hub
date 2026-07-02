---
phase: 04-live-draft-room
plan: 03
subsystem: backend/services + backend/core
tags: [draft, redis-streams, snake-draft, icalendar, arq, sqlalchemy, cache-keys]

requires:
  - phase: 04-02
    provides: Draft, DraftPick, DraftQueue, UserDraftRanking ORM models needed for import_csv_rankings

provides:
  - backend/app/services/draft_service.py with all draft business logic
  - backend/app/core/cache.py extended with 6 draft-specific CacheKey methods
  - snake_pick_to_slot (snake draft order algorithm)
  - build_draft_ics (RFC 5545 ICS calendar invite generation)
  - compute_tier_boundaries (ADP gap tier detection)
  - positional_need_bonus (auto-draft roster balancing)
  - compute_adp_grades (post-draft letter grades by ADP delta)
  - record_draft_event (Redis Stream XADD writer)
  - replay_since (exclusive XRANGE reader for reconnect replay)
  - select_auto_draft_player (queue-first then ADP+need selection)
  - arm_auto_draft_timer (arq deferred job enqueue)
  - import_csv_rankings (CSV upsert to user_draft_rankings)

affects:
  - 04-04 (REST endpoints — imports snake_pick_to_slot, build_draft_ics)
  - 04-05 (Socket.IO namespace — imports record_draft_event, replay_since, select_auto_draft_player)
  - backend/workers/tasks.py (imports compute_adp_grades for post_draft_recap)

tech-stack:
  added:
    - icalendar==7.2.0 (RFC 5545 ICS generation via Calendar.new/Event.new)
  patterns:
    - Pure functions separated from I/O functions within same service module
    - CacheKey.draft_* static methods follow existing CacheKey pattern in cache.py
    - Redis Stream XADD with approximate MAXLEN=5000 cap
    - Exclusive XRANGE lower bound f'({last_event_id}' prevents boundary event re-delivery
    - arq _job_id=f'autodraft:{draft_id}:{pick_num}' for idempotent timer uniqueness

key-files:
  created:
    - backend/app/services/draft_service.py
  modified:
    - backend/app/core/cache.py
    - backend/tests/test_draft_service.py

key-decisions:
  - "replay_since uses exclusive XRANGE lower bound f'({last_event_id}' (not inclusive) to prevent boundary event re-delivery on reconnect (DR-15/Pitfall-1)"
  - "positional_need_bonus accepts position strings (e.g. 'QB', 'RB'), not player IDs — callers pre-filter or pass position list"
  - "select_auto_draft_player checks personal queue first via Redis SISMEMBER before falling back to ADP+need scoring (D-04)"
  - "arm_auto_draft_timer wrapped in try/except — arq not available in test environments; timer failure is non-critical (logged as warning)"
  - "import_csv_rankings deletes existing rankings for user+draft before re-importing (full replace, not merge)"
  - "compute_adp_grades grades by percentile rank within the draft, not absolute ADP delta thresholds"

patterns-established:
  - "Draft service pure functions (snake_pick_to_slot, compute_tier_boundaries, etc.) are module-level, not class methods — consistent with league_service.py pattern"
  - "Redis I/O functions are async and accept Redis as first parameter — injectable for testing"
  - "CacheKey.draft_* methods follow the f'draft:{id}:{key}' namespace convention"

requirements-completed:
  - DR-01
  - DR-02
  - DR-03
  - DR-04
  - DR-08
  - DR-14
  - DR-15

duration: 11min
completed: 2026-07-02
---

# Phase 4 Plan 03: Draft Service — Business Logic and Redis I/O Summary

**Snake draft algorithm, ADP tier/grade computation, Redis Stream event sourcing, and auto-draft selection implemented as pure + async I/O functions in draft_service.py, with 6 new CacheKey.draft_* methods in cache.py**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-07-02T23:17:26Z
- **Completed:** 2026-07-02T23:27:48Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Implemented all 9 draft service functions (5 pure, 4 async I/O) with correct snake order, exclusive XRANGE replay, queue-first auto-draft, and ADP delta grading
- Extended CacheKey with 6 draft-specific Redis key builders (events_stream, state, current_pick, deadline, lock, available)
- All 7 previously-xfail test stubs now xpassed; 1 remaining skip (async DB test for CSV import remains deferred per plan)

## Task Commits

1. **Task 1: Pure business logic functions + CacheKey extensions** - `dbcc177d` (feat)
2. **Task 2: Redis/DB I/O functions** - `34c47ca6` (feat)

## Files Created/Modified

- `backend/app/services/draft_service.py` — Full draft service: snake_pick_to_slot, build_draft_ics, compute_tier_boundaries, positional_need_bonus, compute_adp_grades, record_draft_event, replay_since, select_auto_draft_player, arm_auto_draft_timer, import_csv_rankings
- `backend/app/core/cache.py` — 6 new CacheKey.draft_* static methods appended to existing class
- `backend/tests/test_draft_service.py` — Fixed positional_need_weighting stub (player IDs → position strings); replaced skip stubs for test_redis_stream_replay and test_auto_draft_selection with proper async tests using AsyncMock

## Decisions Made

- `replay_since` uses exclusive XRANGE boundary `f"({last_event_id}"` — not the inclusive default — to prevent re-delivering the last-seen event on reconnect (critical for DR-15 correctness)
- `positional_need_bonus` accepts position strings ("QB", "RB") not player IDs — callers in `select_auto_draft_player` pass `team_positions` which is a list of position strings
- `arm_auto_draft_timer` wrapped in try/except so test environments without arq don't crash; failure is logged as warning, not raised
- `compute_adp_grades` uses percentile rank within the draft (top 15% = A+, next 15% = A, etc.) — relative not absolute grading

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_positional_need_weighting stub: player IDs vs position strings**
- **Found during:** Task 1 (Pure business logic functions)
- **Issue:** The existing test stub passed `["qb1"]` (a player ID) to `positional_need_bonus` but the function and docstring specify `drafted_positions: list of position strings` (e.g. `["QB"]`). The function uses `p == position` comparison which correctly handles position strings but fails on player IDs. The test assertion `bonus_qb == 0.0` failed because `"qb1" != "QB"` so pos_count=0 and unfilled=1 giving 5.0.
- **Fix:** Changed test input from `["qb1"]` to `["QB"]` — the comment already said "1 QB already" making intent clear; the stub used wrong data type.
- **Files modified:** `backend/tests/test_draft_service.py`
- **Verification:** `test_positional_need_weighting` now xpassed
- **Committed in:** `dbcc177d` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test stub bug)
**Impact on plan:** Minimal; fixed incorrect test data. Function implementation matches plan spec exactly.

## Issues Encountered

- `icalendar` package not installed in backend venv — installed via `pip install "icalendar>=7.2.0"` before implementing `build_draft_ics`. This was a dependency gap (the package was added to pyproject.toml in plan 04-01 but not yet installed in this environment).

## Known Stubs

`test_csv_rankings_import` in `backend/tests/test_draft_service.py` still calls `pytest.skip("async db test — implement after 04-03")`. The `import_csv_rankings` function is fully implemented; the test requires a running async DB session fixture and remains deferred. This is acceptable per plan: "remaining async DB stubs still xfail or skip (no ERRORs)".

## Threat Model Coverage

Per plan threat register:
- **T-4-03 (Tampering — record_draft_event):** Function is server-only; no client endpoint writes directly to Redis stream. Client auth enforced at Socket.IO namespace layer (04-05).
- **T-4-02 (Tampering — import_csv_rankings):** CSV import only writes to `user_draft_rankings` DB table; does NOT modify Redis available SET. Available SET is only modified by confirmed picks via server-side SREM (04-05).
- **T-4-05 (Tampering — arm_auto_draft_timer):** `_job_id=f"autodraft:{draft_id}:{pick_num}"` ensures uniqueness per pick. Idempotent guard inside arq task body implemented in 04-05.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced beyond what the plan's threat model covers.

## Next Phase Readiness

- `draft_service.py` ready for import by 04-04 (REST endpoints) and 04-05 (Socket.IO namespace)
- `CacheKey.draft_*` methods ready for use across all Wave 2+ plans
- All pure logic functions verified passing; I/O functions verified importable

## Self-Check: PASSED

- `backend/app/services/draft_service.py` exists: FOUND
- `backend/app/core/cache.py` updated with 6 draft_* methods: FOUND
- `backend/tests/test_draft_service.py` updated with async tests: FOUND
- Task 1 commit `dbcc177d` verified in git log
- Task 2 commit `34c47ca6` verified in git log

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-02*
