---
plan: "03-11"
status: complete
completed_at: "2026-06-29"
---

# 03-11 Summary — ESPN routes + ConnectPage multi-platform UI + credential health cron

## What was built

- `backend/app/api/v1/espn.py` (new):
  - `POST /espn/connect` — private league via SWID + espn_s2 cookies; 401 on bad cookies, 404 on not found; rate-limited
  - `POST /espn/public` — public league via league_id only; 403 if private, 404 if not found; rate-limited

- `backend/workers/tasks.py` — Added `check_platform_credentials`:
  - Queries all `UserCredential` rows where `is_healthy=True`
  - Yahoo: calls `get_game_key()`; marks unhealthy on `YahooAuthExpired`
  - ESPN private: calls `get_league_settings()`; marks unhealthy on `ESPNAuthExpired`
  - Uses ephemeral engine (no FastAPI DI coupling, safe for arq worker context)
  - Cron: every 6 hours (0:30, 6:30, 12:30, 18:30 UTC)

- `frontend/src/pages/ConnectPage.tsx` — Major extension:
  - Step types: `'platform' | 'username' | 'leagues' | 'importing' | 'done' | 'espn_type' | 'espn_private' | 'espn_public' | 'yahoo_connected'`
  - Platform pills: Sleeper, Yahoo (→ server-side OAuth redirect), ESPN (→ espn_type step)
  - ESPN private form: SWID + espn_s2 + league_id; `aria-label` for Playwright targeting; inline error display
  - ESPN public form: league_id only
  - `?platform=yahoo` → opens at `yahoo_connected` step (OAuth callback flow)
  - `?reconnect=*` → opens onboarding at `platform` step (user can re-choose platform)

- `frontend/src/components/ui/PlatformIcon.tsx` (new):
  - `Y!` (purple/bg-purple-600), `E` (red/bg-red-600), `S` (green/bg-green-500)

## Key design decisions
- ESPN SWID/espn_s2 as `type="text"` not password: users paste from DevTools and need to see the value
- `?reconnect=*` opens platform selection (not forced to the original platform) so users can switch platforms during reconnect flow
- Ephemeral engine in `check_platform_credentials`: arq worker has no FastAPI request context, so task creates its own async engine + sessionmaker to avoid DI coupling
