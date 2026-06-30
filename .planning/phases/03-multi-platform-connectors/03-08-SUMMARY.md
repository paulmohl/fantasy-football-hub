---
plan: "03-08"
status: complete
completed_at: "2026-06-29"
---

# 03-08 Summary — Credential health: /users/me extension, HealthBanner, auth store unhealthyPlatforms

## What was built

- `backend/app/api/v1/users.py` — Extended GET /users/me to return `credential_health`:
  - Queries all `UserCredential` rows for the current user
  - Returns `[{platform, is_healthy}]` list
  - Full response: `{id, email, is_verified, has_leagues, created_at, credential_health}`

- `frontend/src/store/auth.ts` — Added `unhealthyPlatforms: string[]` to `AuthState`:
  - `setUnhealthyPlatforms(platforms: string[])` action
  - `clearAuth()` resets `unhealthyPlatforms: []`

- `frontend/src/components/HealthBanner.tsx` (new):
  - Reads `unhealthyPlatforms` from auth store
  - Renders amber banner above main content for each unhealthy platform
  - Shows reconnect link per platform (`/connect?reconnect={platform}`)

- `frontend/src/components/Layout.tsx` — Added `<HealthBanner />` above `<main>`:
  - Renders conditionally (returns null when no unhealthy platforms)

- `frontend/src/App.tsx` — `RequireAuth` fetches `/api/v1/users/me` on token change:
  - Calls `setHasLeagues(data.has_leagues)`
  - Calls `setUnhealthyPlatforms(unhealthy)` with filtered list

## Tests
- `backend/tests/test_users.py` — Extended with `credential_health` assertions and unhealthy credential test
