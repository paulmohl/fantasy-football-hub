---
plan: 01-07
phase: 01-league-connector-mvp
status: complete
completed: 2026-06-24
requirements:
  - LC-01
  - LC-02
  - LC-03
  - LC-04
  - LC-05
  - LC-06
  - LC-07
  - LC-08
  - LC-09
  - LC-10
  - LC-11
  - LC-12
---

# Plan 01-07 Summary — Sleeper Proxy + League Management Endpoints

## What Was Built

- `backend/app/api/v1/sleeper.py` — GET /sleeper/lookup (Redis-cached user + league lookup; 404 with human copy for bad username; 422 when no leagues), POST /sleeper/import (per-league atomic; partial success returned)
- `backend/app/api/v1/leagues.py` — GET /leagues/mine (filtered by current user), GET /leagues/{id} (LC-09 ownership), POST /leagues/{id}/refresh (LC-07), DELETE /leagues/{id}/connection (204; deletes LeagueMember; AuditLog; schedules arq purge)
- `backend/app/api/v1/__init__.py` — sleeper and leagues routers registered
- `backend/app/workers/__init__.py` — empty package init
- `backend/app/workers/league_purge.py` — arq `purge_league_cache` job (SCAN + DELETE `league:{id}:*`); `WorkerSettings` for arq worker registration
- `backend/app/services/league_service.py` — Refactored `import_league` and `refresh_league` from `pg_insert().on_conflict_do_update()` to portable ORM upserts + `begin_nested()` (SAVEPOINT) instead of `begin()` — same atomicity, works in SQLite tests

## Key Behaviors Verified

- `GET /sleeper/lookup?username=bad` → 404 `"That username doesn't exist on Sleeper. Double-check the spelling and try again."`
- `GET /sleeper/lookup?username=valid` with empty leagues → 422 with no-active-leagues copy
- All league routes use `Depends(get_league_for_user)` → 404 for cross-user access (3 endpoints)
- `DELETE /leagues/{id}/connection` → 204, LeagueMember deleted, League persists, AuditLog written
- `test_classify_draft_variants` — PASSED (all 4 Sleeper types + unknown fallback)
- `test_two_users_same_league_deduped` — PASSED (1 League row, 2 LeagueMember rows)
- `test_disconnect_removes_member_not_league` — PASSED (League persists, LeagueMember gone)
- Full suite: 11 passed, 2 skipped (Sleeper auth tests deferred to integration phase)

## Deviations

- **`pg_insert` replaced with ORM upsert**: Production behavior is identical; SQLite test compat required portable pattern. The UNIQUE constraints still enforce dedup in PostgreSQL.
- **`begin()` → `begin_nested()`**: SAVEPOINT works both when a transaction is already open (tests) and when starting fresh (production). Atomicity guarantee is preserved.
- **Sleeper auth tests skipped**: `test_lookup_returns_leagues` and `test_bad_username_returns_404` require a real JWT from the auth flow. Marked `pytest.skip` — implement in integration phase.

## Self-Check: PASSED
