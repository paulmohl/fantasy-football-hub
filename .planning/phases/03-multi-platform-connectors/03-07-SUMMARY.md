---
plan: "03-07"
status: complete
completed_at: "2026-06-29"
---

# 03-07 Summary — PlayerCrossMapService: CSV seed, fuzzy fallback, arq weekly refresh

## What was built

- `backend/app/services/player_id_mapper.py` — `PlayerIDMapper` class:
  - `yahoo_to_sleeper(db, yahoo_id, full_name, position, team)` → sleeper_id | None
  - `espn_to_sleeper(db, espn_id, full_name, position, team)` → sleeper_id | None
  - `_fuzzy_lookup(db, full_name, position, team)` — SequenceMatcher with `FUZZY_THRESHOLD = 0.85`; team as tiebreaker to prevent false positives

- `backend/app/data/player_cross_map_seed.py`:
  - `load_player_cross_map_from_csv(csv_text, db)` — dialect-aware upsert (PostgreSQL: ON CONFLICT DO UPDATE; SQLite: row-by-row fallback)
  - `FFB_IDS_URL`, `FALLBACK_URL` constants

- `backend/workers/tasks.py` — extended with:
  - `seed_player_cross_map(ctx)` — downloads ffb_ids CSV, calls load_player_cross_map_from_csv
  - `WorkerSettings.functions` now includes `seed_player_cross_map`
  - Weekly cron: Monday 02:00 UTC

## Tests (8 tests in test_player_id_mapper.py)

- Direct lookup: yahoo_to_sleeper / espn_to_sleeper returns sleeper_id from DB
- Not found: returns None without raising
- Fuzzy high confidence (ratio > 0.85): returns match
- Fuzzy below threshold: returns None
- Fuzzy team guard: same name + position but different team → returns None
- CSV bulk upsert: 3 rows seeded, second call deduplicates
- CSV missing sleeper_id: row skipped
