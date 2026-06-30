---
plan: "03-05"
status: complete
completed_at: "2026-06-29"
---

# 03-05 Summary — yahoo_service: import Yahoo leagues into unified models

## What was built

- `backend/app/services/yahoo_service.py`:
  - `YAHOO_STAT_MAP` — mapping of Yahoo stat IDs to normalized names (pass_yd, rec, etc.)
  - `YAHOO_FLEX_MAP` — W/R/T → FLEX, Q/W/R/T → SUPERFLEX, etc.
  - `normalize_yahoo_scoring(settings_data)` → `{platform_raw, normalized, keeper_settings}`
  - `normalize_yahoo_roster_format(settings_data)` → `{positions: [...]}`
  - `import_yahoo_league(league_id, game_key, current_user, db, redis, yahoo, week)` — fetch-first, write-atomic
  - `refresh_yahoo_league(league, current_user, db, redis, yahoo, week)` — delegates to import_yahoo_league

## Tests (10 tests in test_league_service.py)

- normalize_yahoo_scoring: PPR rec=1.0, standard rec=0.0, keeper extraction, unmodeled_rules
- normalize_yahoo_roster_format: W/R/T → FLEX, Q/W/R/T → SUPERFLEX, W/T → FLEX, W/R → FLEX
- import_yahoo_league: keeper_flag=True when max_keepers>0, data completeness check, MP-09 keeper extraction
- Roster snapshot: players list has yahoo_id, sleeper_id (None when unmapped), selected_position, is_starting
