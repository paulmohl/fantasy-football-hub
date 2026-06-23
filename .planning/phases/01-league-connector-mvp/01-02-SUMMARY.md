---
phase: 01-league-connector-mvp
plan: 02
subsystem: database
tags: [sqlalchemy, alembic, postgres, jsonb, migrations, models]

# Dependency graph
requires:
  - phase: 00-setup
    provides: FastAPI scaffold, Alembic env.py with async engine, Base class in database.py
provides:
  - SQLAlchemy 2.0 User and Session models (users, sessions tables)
  - SQLAlchemy 2.0 League, LeagueMember, Team, Roster models (leagues, league_members, teams, rosters tables)
  - SQLAlchemy 2.0 AuditLog model (audit_log table)
  - app/models/__init__.py registering all models with Base for Alembic
  - Alembic migration 001_phase1_auth_league creating all 7 Phase 1 tables
affects: [01-03, 01-04, 01-05, 01-06, auth, sleeper, leagues]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SQLAlchemy 2.0 Mapped[T] + mapped_column() declarative style
    - JSONB columns for scoring_rules, roster_format, rosters.snapshot, audit_log.metadata
    - UniqueConstraint on composite keys (host_platform+host_league_id+season, user_id+league_id)
    - metadata_ Python attribute aliased to "metadata" column to avoid SQLAlchemy reserved name conflict
    - Manual migration file matching autogenerate output (when Postgres unavailable in CI)

key-files:
  created:
    - backend/app/models/user.py
    - backend/app/models/league.py
    - backend/app/models/audit.py
    - backend/alembic/versions/001_phase1_auth_league.py
  modified:
    - backend/app/models/__init__.py

key-decisions:
  - "Alembic migration written manually: Docker/Postgres not accessible from bash on Windows — migration schema written by hand to match model definitions exactly"
  - "metadata_ attribute: Python attribute named metadata_ (mapped to 'metadata' column) avoids SQLAlchemy MetaData reserved attribute conflict on DeclarativeBase"
  - "LeagueMember has own PK (id UUID): plan specified id column — keeps standard REST ID semantics even though user_id+league_id is the uniqueness key"

patterns-established:
  - "Model imports: all models imported in __init__.py with noqa: F401 so alembic/env.py import app.models registers everything"
  - "ForeignKey ondelete: CASCADE on user-owned data (sessions, league_members, teams, rosters); SET NULL on audit trail (audit_log.user_id)"
  - "JSONB fields: store raw Sleeper API responses verbatim before validation"

requirements-completed: [LC-09, LC-10, LC-11]

# Metrics
duration: 8min
completed: 2026-06-23
---

# Phase 1 Plan 02: Database Models and Alembic Migration Summary

**SQLAlchemy 2.0 models for 7 Phase 1 tables (users, sessions, leagues, league_members, teams, rosters, audit_log) with JSONB fields and Alembic migration**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-23T16:10:45Z
- **Completed:** 2026-06-23T16:18:49Z
- **Tasks:** 2 of 2
- **Files modified:** 5

## Accomplishments
- User + Session models with hashed refresh token storage, envelope key, and google_sub unique constraint
- League + LeagueMember + Team + Roster models with JSONB columns and dedup constraints
- AuditLog model with metadata_ aliased column to avoid SQLAlchemy reserved name conflict
- app/models/__init__.py wiring all models into Base.metadata for Alembic discovery
- Alembic migration 001_phase1_auth_league covering all 7 Phase 1 tables

## Task Commits

Each task was committed atomically:

1. **Task 1: SQLAlchemy models (user.py, league.py, audit.py)** - `ae0b87e` (feat)
2. **Task 2: Register models in __init__.py and add Alembic migration** - `9e1f3c8` (feat)

**Plan metadata:** committed with SUMMARY.md

## Files Created/Modified
- `backend/app/models/user.py` - User (email, password_hash, google_sub, envelope_key) + Session (token_hash, expires_at) models
- `backend/app/models/league.py` - League (UNIQUE host_platform+host_league_id+season, JSONB scoring_rules+roster_format) + LeagueMember (UNIQUE user_id+league_id) + Team + Roster models
- `backend/app/models/audit.py` - AuditLog with metadata_ → "metadata" JSONB column
- `backend/app/models/__init__.py` - Imports all 7 model classes for Alembic discovery
- `backend/alembic/versions/001_phase1_auth_league.py` - Migration creating all 7 tables with correct FKs and constraints

## Decisions Made
- Wrote migration manually because Docker Desktop is installed on Windows but docker CLI is not accessible from Git Bash (not on PATH). Schema written to match models exactly. `alembic upgrade head` will run when Postgres is available in normal dev workflow.
- `metadata_` attribute name: SQLAlchemy's `DeclarativeBase` exposes a `.metadata` attribute; naming the column attribute the same would shadow it. Used `metadata_` as the Python name with `"metadata"` as the SQL column name via the first positional arg to `mapped_column`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Manual migration instead of alembic autogenerate**
- **Found during:** Task 2 (Generate Alembic migration)
- **Issue:** `alembic revision --autogenerate` requires a live Postgres connection. Docker Desktop is installed but the `docker` CLI is not on the Git Bash PATH on this Windows system. Port 5432 was confirmed closed.
- **Fix:** Wrote `001_phase1_auth_league.py` manually using `op.create_table()` to match all 7 model definitions exactly, including JSONB column types, ForeignKey ondelete behaviors, UniqueConstraints, and composite primary keys.
- **Files modified:** backend/alembic/versions/001_phase1_auth_league.py
- **Verification:** `python -c "import app.models; from app.core.database import Base; ..."` confirms all 7 tables registered in Base.metadata. Migration file syntax verified via Python import.
- **Committed in:** 9e1f3c8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Migration schema accurately reflects models. `alembic upgrade head` will execute cleanly when Postgres is running. No scope creep.

## Issues Encountered
- Docker CLI not on Git Bash PATH on Windows. Postgres unavailable. Resolved by writing migration manually.
- Python 3.14 (Windows Store alias) intercepts `python3` command. Used Python 3.12 at `C:\Users\paul_\AppData\Local\Programs\Python\Python312\python.exe` for verification. `psycopg[binary]` and `sqlalchemy` installed into that environment for import testing.

## User Setup Required
None - no external service configuration required for this plan. Running `alembic upgrade head` requires Postgres (via Docker Compose) to be started by the developer before running migrations.

## Next Phase Readiness
- All 7 Phase 1 tables defined as SQLAlchemy models and migration ready to apply
- Plans 01-03 through 01-06 can now import these models to build auth endpoints, sleeper service, and league connector
- Run `docker compose up -d postgres && cd backend && alembic upgrade head` to apply migration to local Postgres

---
*Phase: 01-league-connector-mvp*
*Completed: 2026-06-23*
