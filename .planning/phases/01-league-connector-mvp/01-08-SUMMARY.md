---
plan: 01-08
phase: 01-league-connector-mvp
status: complete
completed: 2026-06-24
requirements:
  - AUTH-04
---

# Plan 01-08 Summary — Frontend Auth Foundation

## What Was Built

- `frontend/src/lib/api.ts` — Added `withCredentials: true`; replaced simple 401 redirect with refresh retry queue pattern (`isRefreshing` guard, `failedQueue`, calls POST /auth/refresh, updates Zustand, retries original request, clears auth and redirects on failure)
- `frontend/src/store/auth.ts` — Added `hasLeagues: boolean` field, `setHasLeagues` action; `clearAuth` now resets `hasLeagues: false`
- `frontend/src/App.tsx` — Added `RequireLeague` guard (redirects to /connect when hasLeagues=false); wrapped Team/Draft/Trades routes with it; added `/auth/callback` route (`AuthCallback` component reads ?token= and ?user_id=, calls setAuth, redirects to /connect)
- `frontend/src/components/Layout.tsx` — Reads `hasLeagues` from Zustand; `REQUIRES_LEAGUE` const; disabled tabs get `opacity-40 pointer-events-none text-muted aria-disabled tabIndex=-1`; nav label updated to `text-xs font-semibold`

## Key Behaviors Verified

- `npx tsc --noEmit` → 0 errors
- `withCredentials: true` in api.ts axios config
- `isRefreshing` + `failedQueue` pattern prevents duplicate refresh calls on concurrent 401s
- `hasLeagues` never in URL or localStorage separately — derived from /users/me response and persisted in `ffhub-auth` store
- `clearAuth` resets `hasLeagues: false`
- Team, Draft, Trades tabs: `opacity-40 pointer-events-none` when `hasLeagues=false`

## Self-Check: PASSED
