---
phase: 02-team-manager-core
plan: "01"
subsystem: backend-tests, frontend-deps
tags: [testing, wave-0, scaffolding, npm]
dependency_graph:
  requires: []
  provides:
    - backend/tests/test_lineup_optimizer.py
    - backend/tests/test_waiver_ranker.py
    - backend/tests/test_weather_service.py
    - backend/tests/test_team_routes.py
    - backend/tests/fixtures/fc_values_sample.json
    - backend/tests/fixtures/sleeper_players_sample.json
    - frontend/@dnd-kit/core
    - frontend/@dnd-kit/sortable
    - frontend/recharts
  affects:
    - All Wave 1-3 backend plans (test files they must make green)
    - All Wave 4-6 frontend plans (npm packages they import)
tech_stack:
  added:
    - pytest 9.1.1 (dev dep installed in Dockerfile via pip install .[dev])
    - pytest-asyncio 1.4.0
    - aiosqlite 0.22.1
    - "@dnd-kit/core@^6.3.1"
    - "@dnd-kit/sortable@^10.0.0"
    - "recharts@^3.9.0"
  patterns:
    - pytest.importorskip for Wave 0 red-state stubs (tests skip gracefully until module exists)
    - pytest.skip for route stubs (all test_team_routes.py tests skip until Wave 3)
    - Fixture JSON files with deterministic player data keyed by sleeperId
key_files:
  created:
    - backend/tests/test_lineup_optimizer.py
    - backend/tests/test_waiver_ranker.py
    - backend/tests/test_weather_service.py
    - backend/tests/test_team_routes.py
    - backend/tests/fixtures/__init__.py
    - backend/tests/fixtures/fc_values_sample.json
    - backend/tests/fixtures/sleeper_players_sample.json
  modified:
    - backend/Dockerfile (add [dev] to pip install for pytest availability)
    - frontend/package.json (three new dependencies added)
    - frontend/package-lock.json (generated)
decisions:
  - Installed pytest dev deps in Dockerfile via pip install .[dev] — pytest was absent from container preventing any test collection (Rule 2 auto-fix)
  - Used pytest.importorskip instead of NotImplementedError stubs — cleaner red-state pattern, tests skip gracefully rather than erroring
metrics:
  duration: "~15 minutes"
  completed: "2026-06-27T10:52:44Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 7
  files_modified: 3
---

# Phase 02 Plan 01: Wave 0 Test Scaffolding Summary

**One-liner:** Wave 0 pytest stubs with importorskip guards for all three team manager services, plus deterministic 25-player fixture data and three pinned frontend npm packages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create pytest test stubs for backend services | 0f32c88 | 7 files created, Dockerfile updated |
| 2 | Install frontend npm packages | 2d6859a | package.json + package-lock.json |

## What Was Built

### Backend Test Files (Wave 0 stubs)

**`backend/tests/test_lineup_optimizer.py`** — 4 tests covering TM-01 and TM-04:
- `test_optimal_lineup_assigns_starters` — 7 starters filled with confidence scores 0-100
- `test_injured_player_excluded` — OUT player absent from starter slots
- `test_out_replacement` — OUT player entry has replacement_suggestion field
- `test_empty_slot_ids_filtered` — Sleeper empty slot IDs ("0", "") ignored

**`backend/tests/test_waiver_ranker.py`** — 4 tests covering TM-05, TM-06, TM-07:
- `test_minimum_30_targets` — rank_waiver_wire returns >= 30 results
- `test_trend_vs_composite` — score_waiver_player returns both score types, which differ
- `test_in_progress_player_excluded_from_drops` — in-progress player absent, <=3 candidates
- `test_waiver_type_detection` — waiver_type=2 → faab, waiver_type=0 → rolling

**`backend/tests/test_weather_service.py`** — 3 tests covering TM-09:
- `test_indoor_no_chip` — LV (Allegiant, indoor) returns None
- `test_wind_threshold` — wind >= 20 mph triggers chip, < 20 does not
- `test_wind_unit_is_mph` — source inspection confirms wind_speed_unit=mph in API call

**`backend/tests/test_team_routes.py`** — 5 route integration test stubs (all skip):
- test_get_my_team_returns_200, test_get_lineup_returns_optimal, test_get_waiver_returns_ranked_list, test_waiver_type_detection_in_response, test_team_isolation

### Fixture Data

**`backend/tests/fixtures/fc_values_sample.json`** — 20 entries, verified FantasyCalc shape:
- Positions: QB×2, RB×5, WR×5, TE×3, K×1, bench×4
- sleeperId "1001"–"1020" matching sleeper fixture keys
- Values range 500–10000 for meaningful sort tests

**`backend/tests/fixtures/sleeper_players_sample.json`** — 25 entries (dict keyed by player_id):
- 20 entries matching fc_values sleeperId values
- 5 sleeper-only bench players (IDs "2001"–"2005")
- All entries have fantasy_positions, injury_status (null), status, search_rank, depth_chart_order

### Frontend Packages

All three packages installed in frontend container and added to `frontend/package.json`:
- `@dnd-kit/core@^6.3.1` — drag-and-drop primitives for lineup card reordering
- `@dnd-kit/sortable@^10.0.0` — sortable list abstraction for lineup slots
- `recharts@^3.9.0` — trend charts for player detail and waiver value views

## Verification

```
pytest tests/test_lineup_optimizer.py tests/test_waiver_ranker.py tests/test_weather_service.py tests/test_team_routes.py -v
16 skipped, 5 warnings in 0.36s
```

All 16 tests collected with 0 import errors. All skip cleanly (importorskip pattern for service tests, explicit pytest.skip for route tests).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] pytest dev dependencies not installed in container**
- **Found during:** Task 1 verification
- **Issue:** `pip install .` in Dockerfile only installs production deps; pytest/aiosqlite in `[dev]` optional group were absent from container
- **Fix:** Changed `pip install --no-cache-dir .` to `pip install --no-cache-dir ".[dev]"` in `backend/Dockerfile`
- **Files modified:** `backend/Dockerfile`
- **Commit:** 0f32c88

## Known Stubs

None — this plan IS the stub layer. All test files are intentionally in red/skip state. The stubs are the output artifact, not a gap.

## Threat Flags

None — test fixtures are developer-only, no production trust boundary crossed (T-02-01-01 accepted).

## Self-Check: PASSED
