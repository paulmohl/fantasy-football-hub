---
plan: 01-04
phase: 01-league-connector-mvp
status: complete
completed: 2026-06-23
requirements:
  - AUTH-01
  - AUTH-03
  - AUTH-04
---

# Plan 01-04 Summary — Email/Password Auth Endpoints

## What Was Built

- `backend/app/services/auth_service.py` — Session creation with SHA-256 hashed refresh tokens, 30-day expiry, rotation, and deletion
- `backend/app/services/email_service.py` — fastapi-mail wrapper for verification + reset emails; gracefully no-ops when MAIL_SERVER is empty
- `backend/app/api/v1/auth.py` — 8 endpoints: POST /register (201), POST /login, POST /logout (204), POST /refresh, GET /verify-email, POST /forgot-password (always 200), POST /reset-password, POST /resend-verification
- `backend/app/api/v1/users.py` — GET /users/me returning {id, email, is_verified, has_leagues}
- `backend/app/api/v1/__init__.py` — added auth and users routers
- `backend/app/main.py` — added SessionMiddleware (required for Google OAuth in Plan 05)

## Deviations

- **bcrypt<4 pin added** — passlib 1.7.4 is incompatible with bcrypt 4.x (`__about__` attribute removed). Pinned `bcrypt>=3.2.0,<4` in pyproject.toml.
- **JSONB→JSON SQLite patch in conftest.py** — SQLite test engine can't render PostgreSQL JSONB columns. Added `_patch_jsonb_for_sqlite()` that mutates Base.metadata before `create_all`. Production Postgres behavior unchanged.
- **Executed inline** — worktree subagent was denied Bash permission; plan executed directly by orchestrator.

## Test Results

```
6 passed in 1.96s
tests/test_auth.py: 5 tests (register, unverified login, forgot-password no-enum, duplicate 409, verified login)
tests/test_users.py: 1 test (me endpoint has_leagues=False for new user)
```

## Key Files

- `backend/app/api/v1/auth.py` — auth router prefix=/auth
- `backend/app/api/v1/users.py` — users router prefix=/users
- `backend/app/services/auth_service.py` — SHA-256 session management
- `backend/app/services/email_service.py` — SMTP no-op in dev

## Self-Check: PASSED
