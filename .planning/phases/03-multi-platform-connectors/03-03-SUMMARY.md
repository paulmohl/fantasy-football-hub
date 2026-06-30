---
plan: "03-03"
status: complete
completed_at: "2026-06-29"
---

# 03-03 Summary — YahooClient: OAuth flow, token refresh, Fantasy API wrapper

## What was built

- `backend/app/services/yahoo_client.py` — `YahooClient` class:
  - `__init__(http, access_token)` — sets `Accept: application/json` + `Authorization: Bearer` headers
  - `_get(url, params)` — raises `YahooAuthExpired` on 401; raises_for_status on other errors
  - `get_game_key()` — fetches from `/games;game_codes=nfl` at runtime, never hardcoded
  - `get_user_leagues()` — parses nested Yahoo JSON structure
  - `get_league_settings(league_key)`, `get_league_teams(league_key)`, `get_team_roster(team_key, week)`
  - `refresh_access_token(http, refresh_token)` — static method; Basic auth with client_id:client_secret; raises `YahooAuthExpired` on 401
  - `get_yahoo_client(access_token)` — FastAPI dependency factory
- `backend/app/core/config.py` — added `espn_api_base` setting
- `backend/tests/fixtures/yahoo_league.json` — minimal valid Yahoo API response fixture

## Tests

All 8 tests pass (`tests/test_yahoo_client.py`):
- `get_user_leagues` returns list of league dicts from fixture
- 401 raises `YahooAuthExpired`
- `get_game_key` makes API call (not hardcoded)
- `get_league_settings` and `get_team_roster` return raw dict
- `refresh_access_token` returns new tokens on 200, raises `YahooAuthExpired` on 401
- `Accept: application/json` present on every request
