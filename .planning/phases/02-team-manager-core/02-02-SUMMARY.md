---
phase: 02-team-manager-core
plan: "02"
subsystem: backend-data-foundation
tags: [cache, stadium-data, projection-service, fantasycalc, sleeper, redis, tdd]
dependency_graph:
  requires:
    - backend/app/core/cache.py (existing CacheKey/CacheTTL from Phase 1)
    - backend/app/core/redis.py (get_redis dependency)
    - backend/app/core/logging.py (logger)
    - backend/tests/fixtures/fc_values_sample.json (from Plan 01)
  provides:
    - backend/app/core/cache.py (extended with 5 new CacheKey methods + 5 CacheTTL constants)
    - backend/app/data/nfl_stadiums.py (32-team static lookup with indoor flags)
    - backend/app/data/__init__.py
    - backend/app/services/projection_service.py (ProjectionService, FantasyCalcError, get_projection_service)
    - backend/tests/test_cache_and_stadiums.py
    - backend/tests/test_projection_service.py
  affects:
    - WeatherService (Plan 03) — depends on nfl_stadiums.py and CacheKey.open_meteo_weather
    - LineupOptimizer (Wave 2) — depends on ProjectionService.get_fantasycalc_values and build_sleeper_id_index
    - WaiverRanker (Wave 2) — depends on ProjectionService.get_sleeper_trending and get_sleeper_players
tech_stack:
  added: []
  patterns:
    - TDD red/green cycle with pytest.mark.asyncio for async service tests
    - class-with-init dependency injection (http + redis) matching SleeperClient pattern
    - async generator FastAPI dependency (get_projection_service yields)
    - Redis cache-aside with json.dumps/loads and ex=TTL
    - httpx.HTTPStatusError wrapping into domain-specific FantasyCalcError
key_files:
  created:
    - backend/app/data/__init__.py
    - backend/app/data/nfl_stadiums.py
    - backend/app/services/projection_service.py
    - backend/tests/test_cache_and_stadiums.py
    - backend/tests/test_projection_service.py
  modified:
    - backend/app/core/cache.py (5 new CacheKey methods + 5 new CacheTTL constants)
decisions:
  - Used /values/current FantasyCalc endpoint (not deprecated /values?sport=nfl which returns 404)
  - build_sleeper_id_index is synchronous — pure dict comprehension, no I/O needed
  - SoFi Stadium treated as indoor=True for LAC and LAR (weather-controlled despite transparent roof panel)
  - Test source-inspection assertion scoped to actual call site, not docstring mentions of deprecated URL
metrics:
  duration: "~4 minutes"
  completed: "2026-06-27T10:58:51Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 5
  files_modified: 1
---

# Phase 02 Plan 02: Cache/Stadiums/ProjectionService Summary

**One-liner:** Redis cache key extensions for FantasyCalc+Sleeper+weather, 32-team NFL stadium indoor lookup, and ProjectionService merging FantasyCalc values with Sleeper player data via cache-aside pattern.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Test stubs for CacheKey/CacheTTL and NFL stadiums | dc02a81 | test_cache_and_stadiums.py (17 tests) |
| 1 (GREEN) | Extend CacheKey/CacheTTL + create nfl_stadiums.py | 536dfc5 | cache.py, data/__init__.py, data/nfl_stadiums.py |
| 2 (RED) | Test stubs for ProjectionService | ee76023 | test_projection_service.py (16 tests) |
| 2 (GREEN) | Implement ProjectionService | db62f94 | projection_service.py, test_projection_service.py (fix) |

## What Was Built

### cache.py — Extended CacheKey and CacheTTL

**New CacheKey methods (5):**
- `CacheKey.fantasycalc_values(is_dynasty)` → `"fantasycalc:values:redraft"` or `"fantasycalc:values:dynasty"`
- `CacheKey.sleeper_players_nfl()` → `"sleeper:players:nfl"`
- `CacheKey.sleeper_trending_add()` → `"sleeper:trending:add"`
- `CacheKey.sleeper_stats(season, week)` → `"sleeper:stats:2025:1"`
- `CacheKey.open_meteo_weather(team_abbr, date)` → `"weather:KC:2026-09-07"`

**New CacheTTL constants (5):**
- `FANTASYCALC = 86400` (24h — values change infrequently)
- `SLEEPER_PLAYERS = 86400` (24h — 5MB payload, expensive to refetch)
- `SLEEPER_STATS = 3600` (1h — per-week stats finalize after game)
- `SLEEPER_TRENDING = 3600` (1h — in-season add/drop counts)
- `OPEN_METEO = 21600` (6h — once per game day sufficient)

### nfl_stadiums.py — 32-Team Static Lookup

All 32 NFL teams with lat/lon coordinates, indoor flag, and stadium name.

9 indoor/dome teams: LV (Allegiant), LAR (SoFi), LAC (SoFi), IND (Lucas Oil), DET (Ford Field), MIN (US Bank), ATL (Mercedes-Benz), ARI (State Farm), HOU (NRG).

Constants: `WEATHER_WIND_THRESHOLD_MPH = 20`, `WEATHER_RAIN_CODE_THRESHOLD = 63`.

### projection_service.py — ProjectionService

5-method service class following the SleeperClient dependency injection pattern:

- `get_fantasycalc_values(is_dynasty=False)` — fetches `/values/current` with redraft/dynasty params, caches 24h
- `get_sleeper_players()` — fetches full Sleeper player pool (5MB), caches 24h
- `build_sleeper_id_index(fc_values)` — synchronous dict comprehension, maps `sleeperId` → FC entry
- `get_sleeper_trending()` — fetches trending adds, returns `{player_id: count}`, caches 1h
- `get_player_weekly_stats(season, week)` — fetches per-player stats for week, caches 1h

`FantasyCalcError` wraps `httpx.HTTPStatusError` for non-200 FantasyCalc responses.

`get_projection_service()` is an async generator FastAPI dependency yielding `ProjectionService(client, redis)`.

## Verification

```
pytest tests/test_cache_and_stadiums.py tests/test_projection_service.py -v
33 passed, 16 skipped, 14 warnings in 0.42s
```

All Wave 0 stubs still skip cleanly. No regressions in existing test files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Source inspection test falsely flagged deprecated URL in docstring**
- **Found during:** Task 2 GREEN phase
- **Issue:** `test_source_uses_correct_fantasycalc_url` asserted `"sport=nfl" not in source` but the module docstring mentions `/values?sport=nfl` as an anti-pattern comment — causing false failure
- **Fix:** Updated assertion to check the actual `http.get` call site string pattern, not entire source
- **Files modified:** `backend/tests/test_projection_service.py`
- **Commit:** db62f94

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| Task 1 RED | dc02a81 | PASSED — 17 tests failed before implementation |
| Task 1 GREEN | 536dfc5 | PASSED — 17 tests pass after implementation |
| Task 2 RED | ee76023 | PASSED — 16 tests failed before implementation |
| Task 2 GREEN | db62f94 | PASSED — 16 tests pass after implementation |

## Known Stubs

None — all implemented functionality is wired to real logic. No placeholder return values.

## Threat Flags

None — T-02-02-01 and T-02-02-02 mitigations are in place (httpx timeout=15s + Redis 24h cache). T-02-02-03 accepted (static public data).

## Self-Check: PASSED
