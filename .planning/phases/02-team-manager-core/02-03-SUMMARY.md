---
phase: 02-team-manager-core
plan: "03"
subsystem: backend-weather-service
tags: [weather, open-meteo, tdd, redis, httpx, nfl-stadiums]
dependency_graph:
  requires:
    - backend/app/data/nfl_stadiums.py (from Plan 02 — NFL_STADIUMS, WEATHER_WIND_THRESHOLD_MPH, WEATHER_RAIN_CODE_THRESHOLD)
    - backend/app/core/cache.py (from Plan 02 — CacheKey.open_meteo_weather, CacheTTL.OPEN_METEO)
    - backend/app/core/redis.py (get_redis dependency)
    - backend/app/core/logging.py (logger)
    - backend/tests/test_weather_service.py (from Plan 01 — Wave 0 test stubs)
  provides:
    - backend/app/services/weather_service.py (WeatherService, get_weather_service, _should_show_weather_chip)
  affects:
    - Team lineup endpoint (Wave 2) — will call WeatherService.get_game_weather per team in matchup
    - PlayerDetailDrawer (frontend, Wave 2) — renders weather chip from has_chip field
tech_stack:
  added: []
  patterns:
    - TDD importorskip-based RED state (Wave 0 stubs) → GREEN on implementation
    - class-with-init dependency injection (http + redis) matching SleeperClient/ProjectionService pattern
    - async generator FastAPI dependency (get_weather_service yields)
    - Redis cache-aside with json.dumps/loads and ex=CacheTTL.OPEN_METEO
    - httpx.HTTPStatusError wrapping into domain-specific WeatherServiceError
    - Indoor stadium short-circuit before any HTTP call
key_files:
  created:
    - backend/app/services/weather_service.py
  modified:
    - backend/tests/test_weather_service.py (asyncio.run() fix for event loop compatibility)
decisions:
  - asyncio.run() used in test instead of deprecated asyncio.get_event_loop().run_until_complete() — required for Python 3.10+ compatibility when run alongside pytest-asyncio tests
  - Cache even None results (dates outside forecast window) to avoid redundant HTTP calls
  - Kickoff time proxy: prefer 13:00, fall back to 16:00 in forecast data
metrics:
  duration: "~2 minutes"
  completed: "2026-06-27T11:03:23Z"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 1
---

# Phase 02 Plan 03: WeatherService Summary

**One-liner:** Open-Meteo weather fetch for outdoor NFL stadiums with indoor short-circuit, 6h Redis cache, and 20 mph wind/WMO rain/snow chip threshold logic.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (GREEN) | Implement WeatherService with Open-Meteo integration | 39e2195 | weather_service.py, test_weather_service.py (fix) |

## What Was Built

### weather_service.py — WeatherService

**Functions:**
- `_should_show_weather_chip(wind_mph, precipitation_mm, weather_code)` — returns True if weather warrants a chip (wind >= 20 mph, WMO rain code >= 63 or precip >= 2.5mm, WMO snow code 71-77)
- `_extract_kickoff_weather(forecast, game_date)` — extracts weather at 13:00 or 16:00 kickoff slot from Open-Meteo hourly response

**WeatherService class:**
- `get_game_weather(team_abbr, game_date)` — returns None for indoor stadiums without HTTP call; checks Redis cache (key: `weather:{team}:{date}`, TTL: 21600s); fetches Open-Meteo with `wind_speed_unit=mph` param; caches result including None

**FastAPI dependency:**
- `get_weather_service()` — async generator yielding WeatherService with managed httpx client (timeout=15.0s)

**Error handling:**
- `WeatherServiceError` wraps httpx.HTTPStatusError for non-200 Open-Meteo responses

**Threat mitigations applied (per plan threat model):**
- T-02-03-01 (DoS): 6h Redis cache per team+date; httpx timeout=15.0s; cache bypass not possible via API
- T-02-03-02 (Info Disclosure): accepted — returns only public weather data

## Verification

```
pytest tests/test_weather_service.py -v
3 passed, 5 warnings in 0.13s
```

Full suite: 47 passed, 15 skipped, 14 warnings — no regressions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_indoor_no_chip used deprecated asyncio.get_event_loop().run_until_complete()**
- **Found during:** GREEN phase full-suite run
- **Issue:** `asyncio.get_event_loop()` raises `RuntimeError: There is no current event loop in thread 'MainThread'` in Python 3.10+ when run after pytest-asyncio has closed its event loop. The test passed in isolation but failed when run as part of the full suite.
- **Fix:** Replaced with `asyncio.run()` which creates a fresh event loop for the call
- **Files modified:** `backend/tests/test_weather_service.py`
- **Commit:** 39e2195

## TDD Gate Compliance

| Gate | State | Status |
|------|-------|--------|
| RED | Wave 0 stubs used pytest.importorskip — 3 tests SKIPPED before weather_service.py existed | PASSED |
| GREEN | 39e2195 — 3 tests PASSED after implementation | PASSED |

## Known Stubs

None — all implemented functionality is wired to real logic. No placeholder return values.

## Threat Flags

None — all surfaces (Open-Meteo external HTTP) were in the plan's threat model and mitigated.

## Self-Check: PASSED
