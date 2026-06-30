---
plan: "03-10"
status: complete
completed_at: "2026-06-29"
---

# 03-10 Summary — Yahoo OAuth + league import routes

## What was built

- `backend/app/api/v1/oauth.py` — Added Yahoo OAuth registration:
  - `oauth.register("yahoo", ...)` with Yahoo authorize/token URLs and `fspt-w` scope
  - `GET /auth/yahoo` → redirects to Yahoo OAuth consent; returns 503 if not configured
  - `GET /auth/yahoo/callback` → stores credential, auto-refreshes if within 5min of expiry, marks unhealthy on `YahooAuthExpired`, redirects to `/connect?platform=yahoo`

- `backend/app/api/v1/yahoo.py` (new):
  - `_get_yahoo_client_for_user(user, db)` — retrieves credential, handles auto-refresh, marks unhealthy on `YahooAuthExpired`
  - `GET /yahoo/leagues` — returns `{leagues, game_key}`; rate-limited via `check_platform_rate_limit("yahoo")`
  - `POST /yahoo/import` — imports selected leagues by league_key; returns `{imported, errors}`; rate-limited

- `backend/app/api/v1/__init__.py` — Added `yahoo.router` and `espn.router`

- `backend/app/core/config.py` — Added `nfl_season_year: int = 2025`

## Key design decisions
- Server-side OAuth redirect (`window.location.href = '/api/v1/auth/yahoo'`): Yahoo OAuth requires a server-side redirect for the authorization URL; browser-side redirect to `/connect?platform=yahoo` after callback
- Auto-refresh within 5min of expiry: proactive refresh avoids mid-request token expiry
- `YahooAuthExpired` marks credential `is_healthy=False` triggering HealthBanner reconnect prompt
