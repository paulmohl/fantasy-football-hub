---
phase: 04-live-draft-room
plan: 05
subsystem: backend/api + backend/workers + backend/core
tags: [rest-api, draft, arq, fastapi, security, idempotency]
dependency_graph:
  requires:
    - 04-02 (Draft/DraftPick/DraftQueue models)
    - 04-03 (draft_service: build_draft_ics, compute_adp_grades, import_csv_rankings,
             record_draft_event, select_auto_draft_player, arm_auto_draft_timer, snake_pick_to_slot)
  provides:
    - Draft REST API at /api/v1/drafts (6 routes)
    - get_draft_for_user dependency (row-level isolation via league_members JOIN)
    - auto_draft_pick arq task (idempotent clock-expiry handler)
    - post_draft_recap arq task (ADP grade computation after final pick)
  affects:
    - backend/app/api/v1/__init__.py (draft router registered)
    - backend/workers/tasks.py (WorkerSettings.functions extended)
    - All Wave 3+ plans that call draft REST endpoints or trigger arq tasks
tech_stack:
  added: []
  patterns:
    - get_draft_for_user: mirrors get_league_for_user pattern; returns 404 (not 403)
    - Route ordering: literal-path routes registered before parameterized ones (prevents UUID 422)
    - BackgroundTasks for non-blocking ICS email dispatch
    - Redis cache-aside for Sleeper player pool (sleeper:players:nfl key) with httpx fallback
    - arq idempotent guard: check current_pick_num in Redis before DB write
    - AsyncRedisManager(write_only=True) for Socket.IO emit from arq worker context
key_files:
  created:
    - backend/app/api/v1/draft.py
  modified:
    - backend/app/core/deps.py
    - backend/app/api/v1/__init__.py
    - backend/workers/tasks.py
decisions:
  - "Route /league/{league_id} registered before /{draft_id} to prevent Starlette matching literal 'league' as UUID draft_id"
  - "Sleeper player pool fetch uses Redis cache (sleeper:players:nfl) with httpx fallback; SleeperClient not used because it requires injected httpx.AsyncClient and has no get_all_players method"
  - "get_recap injects redis via Depends(get_redis) instead of calling _get_redis() directly"
  - "num_teams hardcoded to 12 in create_draft — League model has no num_teams field"
metrics:
  duration: "~12 minutes"
  completed: "2026-07-03"
  tasks_completed: 2
  files_changed: 4
---

# Phase 4 Plan 05: Draft REST API and arq Tasks Summary

**Draft REST API (6 routes) with commissioner auth, row-level isolation dependency, ICS email dispatch, and arq auto_draft_pick + post_draft_recap tasks with idempotent guards and Socket.IO fan-out**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-03T01:56:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Built all 6 draft REST routes with commissioner role enforcement (T-4-04), CSV validation (T-4-02), and post-draft grades endpoint with value picks / reaches detection (D-13)
- Added `get_draft_for_user` to `deps.py` with JOIN-based row-level isolation returning 404 (T-4-01)
- Added `auto_draft_pick` arq task with T-4-05 idempotent guard, Socket.IO fan-out via `AsyncRedisManager(write_only=True)`, and final-pick detection that enqueues `post_draft_recap`
- Added `post_draft_recap` arq task that computes ADP grades and updates `draft.status = "complete"`
- 154 tests pass, no regressions

## Task Commits

1. **Task 1: Draft REST API + get_draft_for_user + router registration** — `01d456ac` (feat)
2. **Task 2: auto_draft_pick and post_draft_recap arq tasks** — `e26f46e6` (feat)

## Files Created/Modified

- `backend/app/api/v1/draft.py` — 6 REST routes: POST /drafts (DR-01), GET /league/{league_id}, GET /{draft_id}, GET /{draft_id}/recap (DR-14), PUT /{draft_id}/order (DR-02), POST /{draft_id}/rankings (DR-03); ICS background task
- `backend/app/core/deps.py` — `get_draft_for_user` dependency appended after `get_league_for_user`
- `backend/app/api/v1/__init__.py` — `draft` added to imports; `router.include_router(draft.router)` appended
- `backend/workers/tasks.py` — `auto_draft_pick` and `post_draft_recap` functions added; `WorkerSettings.functions` extended to 5 tasks

## Threat Model Coverage

| Threat ID | Mitigation Implemented |
|-----------|----------------------|
| T-4-04 (Elevation) | `POST /drafts` checks `LeagueMember.role in ("commissioner", "owner")` — 403 if not |
| T-4-01 (Spoofing) | `get_draft_for_user` returns 404 for non-member access; never reveals existence |
| T-4-02 (Tampering) | `import_rankings` validates `.csv` extension + UTF-8; `import_csv_rankings` writes only to `user_draft_rankings` table |
| T-4-05 (Tampering) | `auto_draft_pick` checks `current_pick != pick_num - 1` before any DB write |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed route ordering: `/league/{league_id}` before `/{draft_id}`**
- **Found during:** Task 1 (Section B)
- **Issue:** Plan registered `GET /{draft_id}` before `GET /league/{league_id}`. Starlette matches routes in registration order; a request to `/drafts/league/some-id` would bind `draft_id = "league"`, fail UUID validation, and return 422 before reaching the league-list route.
- **Fix:** Registered `/league/{league_id}` first in the router with an explanatory comment.
- **Files modified:** `backend/app/api/v1/draft.py`
- **Commit:** `01d456ac`

**2. [Rule 1 - Bug] Fixed Sleeper player fetch in `update_draft_order`**
- **Found during:** Task 1 (Section B - `lock_and_start` logic)
- **Issue:** Plan imported `from app.services.sleeper import SleeperClient` (wrong path — actual path is `sleeper_client`), called `SleeperClient()` without required `httpx.AsyncClient` arg, and called `get_all_players()` which does not exist on SleeperClient.
- **Fix:** Check `CacheKey.sleeper_players_nfl()` in Redis first; fall back to direct httpx call to `{sleeper_api_base}/players/nfl`. Filter to draftable positions.
- **Files modified:** `backend/app/api/v1/draft.py`
- **Commit:** `01d456ac`

**3. [Rule 1 - Bug] Fixed `get_recap` redis injection**
- **Found during:** Task 1 (Section B - `get_recap` endpoint)
- **Issue:** Plan called `_redis = await _get_redis()` inside `get_recap` body by importing `get_redis` manually. This bypasses FastAPI's dependency injection and creates an unmanaged Redis connection.
- **Fix:** Added `redis: Redis = Depends(get_redis)` as a function parameter; used the injected `redis` directly throughout.
- **Files modified:** `backend/app/api/v1/draft.py`
- **Commit:** `01d456ac`

## Known Stubs

- `num_teams` in `create_draft` is hardcoded to 12 because the `League` model has no `num_teams` field (the count would need to come from the Sleeper/Yahoo/ESPN API response stored at sync time). A future plan that adds `num_teams` to League model or passes it as a request body field should resolve this.
- `team_positions` in `auto_draft_pick` is an empty list — populating it requires a player-position lookup table (player_id → position) not yet available. This means positional need weighting in auto-draft selection is degraded until player metadata is wired.
- `PreDraftLobby.tsx` stub: `PUT /{draft_id}/order` documents in code that import-from-host mode is deferred (W4/OQ1). The frontend plan (04-11) must render a disabled "Import from [Platform]" button per the plan comment.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes beyond what the plan's threat model covers.

## Self-Check: PASSED

- `backend/app/api/v1/draft.py` exists: FOUND
- `backend/app/core/deps.py` contains `get_draft_for_user`: FOUND
- `backend/app/api/v1/__init__.py` contains `draft.router`: FOUND
- `backend/workers/tasks.py` contains `auto_draft_pick` and `post_draft_recap`: FOUND
- Task 1 commit `01d456ac` verified in git log
- Task 2 commit `e26f46e6` verified in git log
- 154 tests pass, 0 failures

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-03*
