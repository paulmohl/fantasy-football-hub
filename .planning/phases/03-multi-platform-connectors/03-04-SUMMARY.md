---
plan: "03-04"
status: complete
completed_at: "2026-06-29"
---

# 03-04 Summary — ESPNClient: cookie-based private auth and public league access

## What was built

- `backend/app/services/espn_client.py` — `ESPNClient` class:
  - `__init__(http, swid=None, espn_s2=None)` — cookies dict populated only when both non-None
  - `get_league(league_id, year)` — multi-view fetch (mSettings, mRoster, mTeam, mMatchupScore, mStandings); raises `ESPNAuthExpired` on 401/403/empty-teams; raises `ESPNLeagueNotFound` on 404
  - `get_league_settings(league_id, year)` — lightweight mSettings-only fetch
  - Custom exceptions: `ESPNAuthExpired`, `ESPNLeagueNotFound` (with `league_id` attribute)
  - Base URL comes from `settings.espn_api_base` — not hardcoded
- `backend/tests/fixtures/espn_league.json` — minimal valid ESPN API response with teams array

## Tests

All 9 tests pass (`tests/test_espn_client.py`):
- Private connect (with SWID + espn_s2): returns teams
- Public connect (no cookies): returns teams, confirms no cookie header sent
- 401 → `ESPNAuthExpired`
- 403 → `ESPNAuthExpired`
- 404 → `ESPNLeagueNotFound` with `league_id` attribute populated
- 200 with no `teams` key → `ESPNAuthExpired` (Pitfall 8)
- 200 with `teams=[]` → `ESPNAuthExpired`
- All required view params present in request
- `client.base` equals `settings.espn_api_base`
