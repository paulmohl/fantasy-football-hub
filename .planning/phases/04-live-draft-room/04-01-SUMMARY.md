---
phase: 04-live-draft-room
plan: "01"
subsystem: test-infrastructure
tags: [wave-0, test-stubs, dependencies, conftest]
dependency_graph:
  requires: []
  provides:
    - mock_redis_streams fixture in conftest.py
    - Wave 0 xfail test stubs for DR-01 through DR-15
    - icalendar package declaration for ICS generation
    - html2canvas package declaration for PNG recap export
  affects:
    - backend/tests/conftest.py
    - backend/pyproject.toml
    - frontend/package.json
tech_stack:
  added:
    - icalendar>=7.2.0 (Python — ICS calendar invite generation)
    - html2canvas@^1.4.0 (npm — draft recap PNG screenshot export)
  patterns:
    - pytest xfail stubs: tests that import from not-yet-created modules mark as xfail so CI tracks DR-* coverage from day one
    - mock_redis_streams fixture: extends mock_redis with realistic Redis Streams return values (xadd/xrange/xlen/sadd/srem/sismember/smembers/scard)
key_files:
  created:
    - backend/tests/test_draft_models.py
    - backend/tests/test_draft_service.py
    - backend/tests/test_draft_namespace.py
    - e2e/tests/uat-10-draft-reconnect.spec.ts
    - e2e/tests/uat-11-draft-flow.spec.ts
  modified:
    - backend/pyproject.toml
    - frontend/package.json
    - backend/tests/conftest.py
decisions:
  - icalendar>=7.2.0 added as runtime dep (not dev) because ICS generation runs in production email handler
  - html2canvas placed in dependencies (not devDependencies) because recap PNG export is a user-facing production feature
  - mock_redis_streams added as separate fixture alongside mock_redis to avoid coupling default Redis mock to Stream-specific return shapes
metrics:
  duration: "6 minutes"
  completed_date: "2026-07-02"
  tasks_completed: 2
  files_changed: 8
---

# Phase 4 Plan 01: Wave 0 Test Infrastructure Summary

**One-liner:** Wave 0 test scaffolding with icalendar + html2canvas deps, Redis Streams mock extensions, and 5 xfail stub test files covering all 15 DR-* requirements.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add missing packages and extend conftest.py Redis mock | 7d47c0c5 | backend/pyproject.toml, frontend/package.json, backend/tests/conftest.py |
| 2 | Create Wave 0 test stub files (failing by design) | e4982fcb | 5 new test files (3 backend, 2 E2E) |

## What Was Built

### Dependency Additions

`backend/pyproject.toml` — `icalendar>=7.2.0` added after `fastapi-mail>=1.6.5` in the `[project] dependencies` list. Used in plan 04-03 for `build_draft_ics()`.

`frontend/package.json` — `html2canvas@^1.4.0` added alphabetically between `clsx` and `lucide-react`. Used in plan 04-11 for `DraftRecap` PNG export.

### conftest.py Extensions

`mock_redis` fixture extended with 8 Redis Streams + Set methods:
- `xadd`, `xrange`, `xlen` — Redis Streams for draft event replay (DR-15)
- `sadd`, `srem`, `sismember`, `smembers`, `scard` — Redis Sets for draft participant tracking

New `mock_redis_streams` fixture added with realistic return values (1 pre-loaded stream entry + 3 tracked players) for tests that need non-empty stream state.

### Wave 0 Test Stub Files

**backend/tests/test_draft_models.py** (3 tests, all xfail):
- `test_draft_model_has_required_fields` — DR-01, DR-02
- `test_draft_pick_unique_constraint_defined` — DR-08
- `test_user_draft_ranking_model_exists` — DR-03

**backend/tests/test_draft_service.py** (8 tests: 5 xfail + 3 skip-within-xfail):
- `test_snake_pick_to_slot` — DR-02 snake draft algorithm
- `test_build_draft_ics` — DR-01 calendar invite
- `test_tier_boundaries` — DR-04 tiered cheat sheet
- `test_positional_need_weighting` — DR-08 auto-draft scoring
- `test_adp_grade_computation` — DR-14 post-draft grades
- Plus 3 async stubs deferred to plan 04-03: `test_auto_draft_selection`, `test_csv_rankings_import`, `test_redis_stream_replay`

**backend/tests/test_draft_namespace.py** (4 tests: 2 xfail + 2 skip-within-xfail):
- `test_pick_propagates` — DR-07 pick propagation
- `test_commissioner_pause` — DR-09 pause/resume
- Plus 2 Socket.IO client stubs deferred to plan 04-04

**e2e/tests/uat-10-draft-reconnect.spec.ts** — DR-15 reconnect + event replay (full test.skip guard, implements in plan 04-13)

**e2e/tests/uat-11-draft-flow.spec.ts** — DR-07, DR-09 full happy path (full test.skip guard, implements in plan 04-13)

### Test Results

```
backend pytest (all 150 prior passing tests + 15 new stubs):
  150 passed, 10 xfailed, 7 skipped — 0 errors
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

All stub test files are intentional xfail stubs. The stubs track which plan will implement the production code:

| Stub | File | Resolved By |
|------|------|-------------|
| app.models.draft import | test_draft_models.py | plan 04-02 |
| app.services.draft_service import | test_draft_service.py | plan 04-03 |
| app.sockets.draft_namespace import | test_draft_namespace.py | plan 04-04 |
| E2E reconnect flow | uat-10-draft-reconnect.spec.ts | plan 04-13 |
| E2E full draft flow | uat-11-draft-flow.spec.ts | plan 04-13 |

These stubs are intentional per the Wave 0 scaffolding design — they are NOT blocking the plan's goal. The plan's goal is to create the scaffolding, which is complete.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced in this plan. All changes are test infrastructure only.

## Self-Check: PASSED

- [x] `backend/tests/test_draft_models.py` exists
- [x] `backend/tests/test_draft_service.py` exists
- [x] `backend/tests/test_draft_namespace.py` exists
- [x] `e2e/tests/uat-10-draft-reconnect.spec.ts` exists
- [x] `e2e/tests/uat-11-draft-flow.spec.ts` exists
- [x] Commit 7d47c0c5 exists (Task 1)
- [x] Commit e4982fcb exists (Task 2)
- [x] `backend/pyproject.toml` contains `icalendar>=7.2.0`
- [x] `frontend/package.json` contains `html2canvas@^1.4.0`
- [x] `conftest.py` mock_redis has xadd, xrange, sadd, srem, sismember
- [x] `conftest.py` has mock_redis_streams fixture
- [x] pytest --co collects 15 stub tests without errors
- [x] All stub tests report xfail (not ERROR)
