---
phase: 04-live-draft-room
plan: 02
subsystem: backend/models + backend/migrations
tags: [models, alembic, draft, sqlalchemy, postgresql]
dependency_graph:
  requires:
    - 04-01 (test scaffolding — conftest.py JSONB patch, mock_redis fixtures)
    - 002_phase3_credentials_playermap (Alembic revision chain)
  provides:
    - Draft, DraftPick, DraftQueue, DraftChatMessage, UserDraftRanking ORM models
    - Alembic migration 003 creating all 5 draft tables
  affects:
    - All Wave 2+ plans that query draft DB tables (04-03 through 04-12)
tech_stack:
  added: []
  patterns:
    - Mapped[T] column style with JSONB for list/dict fields
    - named UniqueConstraint + Index in __table_args__ tuple
    - lambda datetime.now(UTC).replace(tzinfo=None) for tz-naive timestamps
    - sa.JSON() in migration (JSONB in model) for SQLite test compatibility
key_files:
  created:
    - backend/app/models/draft.py
    - backend/alembic/versions/003_draft_models.py
  modified:
    - backend/app/models/__init__.py
decisions:
  - Used named UniqueConstraints for DraftPick (uq_draft_picks_draft_pick_num, uq_draft_picks_draft_player) matching threat model T-4-01/T-4-01b
  - Used sa.JSON() (not sa.JSONB()) in migration to maintain SQLite test compatibility via conftest _patch_jsonb_for_sqlite
  - Used JSONB in models (postgresql-specific) so production Postgres gets binary JSON indexing
  - Exported all 5 models from __init__.py so Base.metadata.create_all picks them up in test fixture
metrics:
  duration: "~5 minutes"
  completed: "2026-07-02"
  tasks_completed: 2
  files_changed: 3
---

# Phase 4 Plan 02: Draft Models and Migration Summary

**One-liner:** Five SQLAlchemy draft ORM models with named constraints/indexes and Alembic migration 003 chained from 002.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create backend/app/models/draft.py with 5 models | f0fc3d0e | backend/app/models/draft.py, backend/app/models/__init__.py |
| 2 | Create Alembic migration 003 and verify | bb44ed13 | backend/alembic/versions/003_draft_models.py |

## What Was Built

### Models (backend/app/models/draft.py)

Five SQLAlchemy ORM models using `Mapped[T]` typed column syntax:

- **Draft**: league scheduling record — `league_id`, `commissioner_user_id`, `status` (pending|live|paused|complete), `scheduled_at`, `timezone`, `pick_clock_seconds`, `num_rounds`, `num_teams`, `current_pick_num`, `pick_deadline_epoch`, JSONB `draft_order`
- **DraftPick**: individual pick records — two named `UniqueConstraint` (draft+pick_num, draft+player_id, enforcing T-4-01/T-4-01b mitigations), JSONB `reactions` dict, `is_auto_pick` flag
- **DraftQueue**: per-user pre-draft queue — `UniqueConstraint` on (draft, user, player), `position` int for sort order
- **DraftChatMessage**: live chat — FK to draft+user, `created_at` indexed for chronological retrieval
- **UserDraftRanking**: per-user custom rankings — `UniqueConstraint` on (draft, user, player), `source` field (fantasycalc|csv|manual)

### Migration (backend/alembic/versions/003_draft_models.py)

- Revision ID: `003_phase4_draft_models`
- Chains from: `002_phase3_credentials_playermap`
- Creates tables in FK dependency order: drafts → draft_picks → draft_queue → draft_chat_messages → user_draft_rankings
- Uses `sa.JSON()` (not `sa.JSONB()`) for JSONB columns — test suite's `_patch_jsonb_for_sqlite` handles the JSONB→JSON swap for SQLite; production Postgres gets native JSONB
- Downgrade drops tables and indexes in reverse order

## Threat Model Coverage

Both T-4-01 threats are mitigated by DB-level constraints:
- **T-4-01 (player drafted twice):** `UniqueConstraint("draft_id", "player_id", name="uq_draft_picks_draft_player")` on `draft_picks`
- **T-4-01b (duplicate pick_num):** `UniqueConstraint("draft_id", "pick_num", name="uq_draft_picks_draft_pick_num")` on `draft_picks`

## Test Results

`pytest tests/test_draft_models.py` — 3 xpassed (tests were marked xfail pending this plan; all pass now).

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan delivers models/migration only. No data flow to UI. No stubs.

## Self-Check: PASSED

- `backend/app/models/draft.py` exists: FOUND
- `backend/alembic/versions/003_draft_models.py` exists: FOUND
- `backend/app/models/__init__.py` updated with draft imports: FOUND
- Commits f0fc3d0e and bb44ed13 verified in git log
