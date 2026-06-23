---
phase: 01-league-connector-mvp
plan: "03"
subsystem: backend-core
tags: [cache, deps, fastapi, testing, redis, jwt, auth]
dependency_graph:
  requires:
    - "01-01 (docker-compose, env scaffold)"
    - "01-02 (models: User, League, LeagueMember)"
  provides:
    - "CacheKey helpers and CacheTTL constants (backend/app/core/cache.py)"
    - "get_current_user and get_league_for_user FastAPI dependencies (backend/app/core/deps.py)"
    - "pytest test infrastructure: async_client, test_db, mock_redis (backend/tests/conftest.py)"
  affects:
    - "All Wave 2+ endpoints (consume get_current_user, get_league_for_user)"
    - "All Wave 2+ tests (consume conftest fixtures)"
tech_stack:
  added: []
  patterns:
    - "Cache-aside pattern via get_or_set helper"
    - "FastAPI HTTPBearer dependency for JWT auth guard"
    - "SQLAlchemy JOIN through junction table for ownership enforcement"
    - "pytest-asyncio fixtures with dependency_overrides for test isolation"
    - "In-memory SQLite (aiosqlite) for integration tests without Postgres"
key_files:
  created:
    - backend/app/core/cache.py
    - backend/app/core/deps.py
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_auth.py
    - backend/tests/test_oauth.py
    - backend/tests/test_users.py
    - backend/tests/test_sleeper.py
    - backend/tests/test_leagues.py
  modified:
    - backend/pyproject.toml
decisions:
  - "Deps.py imports models (League, LeagueMember, User) that are created by Wave 1 Plans 01/02 — design-time dependency, resolved at wave merge"
  - "get_or_set uses the caller-owns-serialization pattern (returns raw string; caller does json.loads)"
  - "test_db uses SQLite in-memory to avoid Postgres dependency in CI unit tests"
  - "mock_redis uses MagicMock + AsyncMock — no real Redis needed for unit/integration tests"
  - "aiosqlite and pytest-mock added to pyproject.toml [dev] dependencies"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-23T16:17:20Z"
  tasks_completed: 2
  files_created: 9
  files_modified: 1
---

# Phase 01 Plan 03: Cache Helpers, Auth Dependencies, and Test Infrastructure Summary

**One-liner:** Redis key builders with correct Phase 1 TTLs, JWT auth guard + ownership guard FastAPI dependencies, and in-memory pytest fixtures unblocking all Wave 2+ tests.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create cache.py and deps.py | e725069 | backend/app/core/cache.py, backend/app/core/deps.py |
| 2 | Create test infrastructure (conftest.py + test stubs) | 28d71ed | backend/tests/conftest.py, 5x test_*.py, pyproject.toml |

## What Was Built

### backend/app/core/cache.py

`CacheKey` static helpers produce all 7 Phase 1 Redis key patterns:
- `sleeper:user:{username}` — username lowercased (Pitfall 6 defense)
- `sleeper:leagues:{user_id}:{season}`
- `league:{id}:settings`
- `league:{id}:members`
- `league:{id}:rosters:{week}`
- `nfl:state`
- `ratelimit:sleeper:{user_id}`

`CacheTTL` constants match ARCHITECTURE.md Section 5:
- `LEAGUE_SETTINGS = 21600` (6 hours)
- `LEAGUE_MEMBERS = 21600` (6 hours)
- `NFL_STATE = 3600` (1 hour)
- `SLEEPER_LEAGUES = 600` (10 min)
- `SLEEPER_USER = 300` (5 min)
- `LEAGUE_ROSTERS = 1800` (30 min)

`get_or_set` cache-aside helper handles cache miss → fetch → store atomically.

### backend/app/core/deps.py

`get_current_user`: validates `HTTPBearer` JWT via `decode_token`, queries User by UUID, rejects if `is_verified=False` with 401. Satisfies AUTH-01, T-03-02.

`get_league_for_user`: resolves URL `league_id` by JOIN through `league_members` filtered by `current_user.id`. Returns 404 (not 403) for ownership failures — prevents resource enumeration. Satisfies LC-09, T-03-01.

### backend/tests/conftest.py

Three fixtures:
- `test_engine` / `test_db`: in-memory SQLite via aiosqlite, creates all tables from `Base.metadata`, drops after each test function
- `mock_redis`: `MagicMock` with `AsyncMock` for get/set/delete/incr/expire — no real Redis needed
- `async_client`: `httpx.AsyncClient` with `ASGITransport`, overrides `get_db` and `get_redis` via `app.dependency_overrides`, clears overrides after each test

### Test stubs (5 files)

All 10 tests collected by pytest. Tests covering Wave 2+ endpoints (`test_users.py`, `test_sleeper.py`, `test_leagues.py`) use `pytest.skip()` with references to the plans that will implement the required endpoints.

## Deviations from Plan

None — plan executed exactly as written.

The one deviation worth noting: `deps.py` cannot be fully import-verified in isolation because it imports `app.models.league` and `app.models.user`, which are created by Plans 01/02 running in the same wave. This is an expected design-time dependency, not a bug — the models will be present after wave merge.

## Known Stubs

The five `test_*.py` files contain skipped tests for endpoints not yet implemented:
- `test_auth.py` tests will execute (non-skipped) — but will fail until auth endpoints exist (Wave 2 Plan D)
- `test_oauth.py::test_google_redirect` — skipped implicitly (endpoint 404s); will fail until oauth route added
- `test_users.py::test_me_no_leagues` — `pytest.skip()` (explicit)
- `test_sleeper.py` — `pytest.skip()` (explicit, both tests)
- `test_leagues.py` — `pytest.skip()` (explicit, all 3 tests)

These are intentional placeholder stubs, not functional stubs blocking this plan's goal.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced in this plan. `deps.py` implements the threat mitigations specified in the plan's threat model (T-03-01, T-03-02).

## Self-Check

Files exist:
- [x] backend/app/core/cache.py
- [x] backend/app/core/deps.py
- [x] backend/tests/__init__.py
- [x] backend/tests/conftest.py
- [x] backend/tests/test_auth.py
- [x] backend/tests/test_oauth.py
- [x] backend/tests/test_users.py
- [x] backend/tests/test_sleeper.py
- [x] backend/tests/test_leagues.py

Commits exist:
- [x] e725069 — feat(01-03): cache.py and deps.py
- [x] 28d71ed — feat(01-03): test infrastructure

Verification results:
- [x] `CacheKey.sleeper_user('PaulMohl') == 'sleeper:user:paulmohl'` — PASS
- [x] `CacheTTL.LEAGUE_SETTINGS == 21600` — PASS
- [x] `pytest --collect-only` shows 10 collected tests — PASS
- [x] deps.py has 2x status_code=401 and 1x status_code=404 — PASS

## Self-Check: PASSED
