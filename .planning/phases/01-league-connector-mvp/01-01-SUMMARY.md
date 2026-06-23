---
phase: 01-league-connector-mvp
plan: 01
subsystem: infrastructure
tags: [docker, jwt, auth, config, dependencies]
requirements: [AUTH-01, AUTH-02, AUTH-03]

dependency_graph:
  requires: []
  provides:
    - docker-compose local dev environment (postgres 16 + redis 7)
    - PyJWT-based token operations in security.py
    - itsdangerous email token helpers
    - refresh cookie setter
    - config.py fields for google oauth, mail, is_production
  affects:
    - backend/app/core/security.py (all callers)
    - backend/app/core/config.py (all callers)

tech_stack:
  added:
    - PyJWT>=2.13.0 (replaces python-jose)
    - authlib>=1.7.2 (Google OAuth)
    - itsdangerous>=2.2.0 (email verification tokens)
    - fastapi-mail>=1.6.5 (transactional email)
    - "@radix-ui/react-checkbox" frontend
    - "@radix-ui/react-label" frontend
  patterns:
    - URLSafeTimedSerializer for email tokens (itsdangerous)
    - httpOnly cookie via Response.set_cookie for refresh token
    - pydantic-settings bool field for is_production (not a property)

key_files:
  created:
    - docker-compose.yml
    - .env.example
  modified:
    - backend/pyproject.toml
    - frontend/package.json
    - backend/app/core/security.py
    - backend/app/core/config.py

decisions:
  - "is_production changed from @property (derived from app_env) to plain bool field to allow env var override without coupling to app_env string"
  - "jwt_expire_minutes fixed from 60*24*7 (7 days) to 15 per T-01-02 threat mitigation"
  - "python-jose removed in same task as PyJWT addition — both export jwt.encode but use different exception classes; co-existence creates silent bugs"

metrics:
  duration_minutes: 5
  completed_date: 2026-06-23T16:15:00Z
  tasks_completed: 2
  files_modified: 6
---

# Phase 1 Plan 01: Dependency Migration and Dev Environment Setup Summary

**One-liner:** PyJWT migration with itsdangerous email tokens, docker-compose local dev stack (postgres 16 + redis 7), and config.py extended with Google OAuth and mail fields.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Docker Compose + dependency installation | a363adf | docker-compose.yml, .env.example, backend/pyproject.toml, frontend/package.json |
| 2 | Migrate security.py to PyJWT + extend config.py | 9a3b690 | backend/app/core/security.py, backend/app/core/config.py |

## What Was Built

**Task 1 — Infrastructure and dependencies:**
- `docker-compose.yml` with four services: postgres 16-alpine, redis 7-alpine, backend (uvicorn --reload), frontend (vite --host). Postgres and redis include healthchecks; backend depends_on both healthy.
- `.env.example` with all required env var names and placeholder values, covering DATABASE_URL, REDIS_URL, JWT_SECRET, APP_SECRET_KEY, Google OAuth, mail settings, and SLEEPER_API_BASE.
- `backend/pyproject.toml`: removed `python-jose[cryptography]>=3.3.0`, added `PyJWT>=2.13.0`, `authlib>=1.7.2`, `itsdangerous>=2.2.0`, `fastapi-mail>=1.6.5`.
- `frontend/package.json`: added `@radix-ui/react-checkbox` and `@radix-ui/react-label`.

**Task 2 — Security and config migration:**
- `backend/app/core/security.py`: replaced `from jose import JWTError, jwt` with `import jwt` (PyJWT) and `from jwt.exceptions import ExpiredSignatureError, InvalidTokenError`. Updated `decode_token` to catch typed exceptions. Added `create_email_token`, `verify_email_token` (itsdangerous URLSafeTimedSerializer), `create_refresh_token` (secrets.token_urlsafe(48)), and `set_refresh_cookie` (httpOnly, samesite=lax, 30-day max_age).
- `backend/app/core/config.py`: fixed `jwt_expire_minutes` from 7 days to 15. Changed `is_production` from a computed `@property` to a plain `bool = False` field (allows env var override). Added `google_client_id`, `google_client_secret`, `google_redirect_uri`, `mail_server`, `mail_port`, `mail_username`, `mail_password`, `mail_from`, `mail_tls`.

## Deviations from Plan

### Auto-adjusted

**1. [Rule 2 - Config] is_production changed from @property to bool field**
- **Found during:** Task 2
- **Issue:** The original config.py had `is_production` as a `@property` returning `self.app_env == "production"`. The plan specified adding `is_production: bool = False` as a field. The field approach is strictly better: it allows direct env var override (`IS_PRODUCTION=true`) without coupling to the `app_env` string value.
- **Fix:** Removed the property, added `is_production: bool = False` as a pydantic-settings field. The `app_env` field is retained for other uses.
- **Files modified:** `backend/app/core/config.py`
- **Commit:** 9a3b690

## Known Stubs

None. This plan is infrastructure-only. No UI components or data endpoints were added.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The `.env.example` file contains only placeholder values (T-01-01: accepted). The `jwt_expire_minutes` fix implements T-01-02 mitigation.

## Self-Check: PASSED

- docker-compose.yml: FOUND
- .env.example: FOUND
- backend/pyproject.toml (PyJWT, authlib, itsdangerous, fastapi-mail): FOUND (4 lines)
- python-jose: REMOVED (grep returns 0 lines)
- frontend/package.json (@radix-ui/react-checkbox): FOUND
- backend/app/core/security.py (import jwt): FOUND
- backend/app/core/config.py (jwt_expire_minutes=15): FOUND
- All 5 security functions importable: VERIFIED (python import test passed)
- Commits a363adf and 9a3b690: FOUND in git log
