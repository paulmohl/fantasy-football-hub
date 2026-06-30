---
plan: "03-06"
status: complete
completed_at: "2026-06-29"
---

# 03-06 Summary — espn_service: import ESPN leagues into unified models

## What was built

- `backend/app/services/espn_service.py`:
  - `ESPN_STAT_MAP` — stat ID to normalized name (pass_yd, rec, etc.)
  - `ESPN_SLOT_MAP` — lineup slot ID to position name (FLEX, SUPERFLEX, BN, IR, etc.)
  - `normalize_espn_scoring(league_data)` → `{platform_raw, normalized, keeper_settings}`
  - `normalize_espn_roster_format(league_data)` → `{positions: [...]}`
  - `import_espn_league(league_id, year, is_public, current_user, db, redis, espn, week)` — fetch-first, write-atomic
  - Public leagues: `LeagueMember.role = "viewer"`
  - All teams from `response["teams"]` are persisted (Pitfall 6 guard)

## Tests (10 tests in test_league_service.py)

- normalize_espn_scoring: PPR rec=1.0, unknown stat → unmodeled_rules, keeper extraction
- normalize_espn_roster_format: slot 23 → FLEX, slot 20 → SUPERFLEX
- import_espn_league: private league host_platform="espn" + keeper_flag, public sets role="viewer"
- Pitfall 6: 3-team ESPN response creates 3 Team rows
- ESPNAuthExpired before DB → no League row written (no partial state)
- Roster snapshot: players list has espn_id, sleeper_id (None when unmapped), lineup_slot_id, is_starting
