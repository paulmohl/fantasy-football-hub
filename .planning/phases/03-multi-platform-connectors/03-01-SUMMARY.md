---
plan: "03-01"
status: complete
completed_at: "2026-06-28"
---

# 03-01 Summary — DB models and Alembic migration for user_credentials and player_cross_map

## What was built

- `backend/app/models/credential.py` — `UserCredential` model: id, user_id (FK→users CASCADE), platform, credentials_encrypted (bytea), is_healthy, last_validated_at, created_at; unique constraint (user_id, platform)
- `backend/app/models/player.py` — `PlayerCrossMap` model: sleeper_id (PK), yahoo_id, espn_id, full_name, position, team, updated_at; indexes on yahoo_id and espn_id
- `backend/app/models/__init__.py` — extended with imports for both new models
- `backend/alembic/versions/002_phase3_credentials_playermap.py` — migration chained to 001_phase1_auth_league; creates both tables with correct constraints and indexes

## Also fixed (Phase 2 UAT gaps)

- `backend/workers/tasks.py` — added `redis_settings = RedisSettings.from_dsn(REDIS_URL)` so arq CLI connects to Docker Redis, not localhost
- `docker-compose.yml` — added `worker` service (`arq workers.tasks.WorkerSettings`) depending on postgres+redis healthchecks

## Verification

- `from app.models.credential import UserCredential; from app.models.player import PlayerCrossMap` → imports ok
- `alembic upgrade head` → ran clean: `001_phase1_auth_league -> 002_phase3_credentials_playermap`
- `\d user_credentials` → uuid PK, bytea credentials_encrypted, unique (user_id, platform), CASCADE FK
- `\d player_cross_map` → varchar PK, indexes on yahoo_id + espn_id
