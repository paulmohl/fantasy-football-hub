---
phase: 04-live-draft-room
plan: 13
subsystem: backend/notifications, backend/draft-api, frontend/app
tags: [fastapi, react, notifications, redis, gap-closure, dr-01]
dependency_graph:
  requires: [04-12]
  provides: [notifications-endpoint, draft-notification-push, toast-on-login]
  affects:
    - backend/app/api/v1/notifications.py
    - backend/app/api/v1/draft.py
    - backend/app/api/v1/__init__.py
    - frontend/src/App.tsx
tech_stack:
  added: []
  patterns: [redis-list-queue, read-once-notification, background-task-push]
key_files:
  created:
    - backend/app/api/v1/notifications.py
  modified:
    - backend/app/api/v1/draft.py
    - backend/app/api/v1/__init__.py
    - frontend/src/App.tsx
decisions:
  - Toast API is toast(message, variant) not addToast({...}) — adapted from plan template
  - useToast already imported in App.tsx — only api import was missing
  - notification_key() helper extracted to notifications.py for consistent key naming
  - decode_responses=True on Redis client means raw.decode() is defensive only
metrics:
  duration: "5 minutes"
  completed: "2026-07-04"
  tasks: 3
  files: 4
---

# Phase 4 Plan 13: Gap Closure — In-App Draft Notifications Summary

**One-liner:** Closed DR-01 in-app notification gap — Redis read-once queue, create_draft push to all members, RequireAuth toast display on login.

## What Was Built

This plan closed Gap 5 (MINOR): DR-01 required in-app notifications when a draft is scheduled, which previously only sent ICS email.

1. **GET /api/v1/notifications** — new `notifications.py` module with `list_notifications` endpoint. Reads Redis list `notifications:{user_id}` via LRANGE, deletes the key after reading (read-once semantics), returns parsed JSON array. JWT-protected via `get_current_user`. T-4-03 satisfied: key is server-derived from JWT user_id.

2. **`_push_draft_notifications` in draft.py** — new background function called by `create_draft` after `db.commit()`. Opens its own DB session (background task pattern matching `_send_draft_invites`), queries all `LeagueMember.user_id` for the league, pushes notification JSON to `notifications:{uid}` with RPUSH, sets 7-day TTL via EXPIRE. Notification shape: `type`, `draft_id`, `league_name`, `message`, `created_at`.

3. **RequireAuth notification fetch (App.tsx)** — added `api` import and `const { toast } = useToast()`. On token change, fires `api.get('/notifications')` (non-blocking with `.catch(() => {})`). Each returned notification is displayed via `toast(n.message, 'info')`. Pre-existing `useToast` import unchanged.

## Commits

| Task | Hash | Description |
|------|------|-------------|
| 1 | 4b3639af | feat(04-13): create GET /notifications endpoint; register in __init__.py |
| 2 | f7db2b67 | feat(04-13): push Redis notifications to all league members on create_draft |
| 3 | 4ba8ae64 | feat(04-13): fetch and display draft notifications as toasts in RequireAuth |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Adaptation] Toast API differs from plan template**
- **Found during:** Task 3
- **Issue:** Plan template used `addToast({ message, type: 'info' })` but the actual Toast component exposes `toast(message, variant)` where variant is `'info' | 'error'`
- **Fix:** Used `toast(n.message, 'info')` to match the existing API
- **Files modified:** `frontend/src/App.tsx`
- **Commit:** 4ba8ae64

## Known Stubs

None — all notification paths are fully wired end-to-end.

## Threat Flags

None — T-4-03 and T-4-05 mitigations satisfied as designed. GET /notifications key is server-derived from JWT; notification push is bounded by league member count with TTL preventing unbounded growth.

## Self-Check: PASSED

- `backend/app/api/v1/notifications.py` — FOUND
- `backend/app/api/v1/__init__.py` — includes notifications router
- `backend/app/api/v1/draft.py` — _push_draft_notifications exists, wired in create_draft
- `frontend/src/App.tsx` — api.get('/notifications'), toast(n.message, 'info') present
- Commits 4b3639af, f7db2b67, 4ba8ae64 — FOUND
- Backend import: `from app.api.v1.notifications import router; from app.api.v1.draft import _push_draft_notifications` — OK
- TypeScript: 0 errors for App.tsx (19 pre-existing @/lib/utils errors out of scope, matches 04-12 baseline)
