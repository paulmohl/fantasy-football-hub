# Bug Log

Found 2026-10-28 via Playwright (mocked API, dev server on :5175) plus code read.
Fixed on branch `fix/team-ownership` (uncommitted): BUG-1, 2, 3, 4, 6, plus BUG-8 below. Open: BUG-5, 7, 9.

## BUG-1: No players or lineup after connecting a league (blocker) — FIXED

**Symptom:** After connecting a league, Team page shows "Team Manager", "Couldn't load lineup", "Couldn't load waiver rankings", "Standings unavailable". No roster visible.

**Root cause:** Nothing in the codebase ever sets `Team.owner_user_id`.
- `backend/app/services/espn_service.py:208` creates `Team(...)` with no owner.
- `backend/app/services/yahoo_service.py:217` same.
- `backend/app/services/league_service.py:154` (Sleeper) sets `owner_user_id=None` explicitly.
- `LeagueMember.host_team_id` is also written as `None` for ESPN (`espn_service.py:187`).

`backend/app/api/v1/team.py:_get_user_team_and_roster` matches on `Team.owner_user_id == current_user.id`, so it always returns `(None, None)` and `/team/lineup` answers 404 "Team not found in this league". `/team/waiver` and `/team/my` (`team_name` is always null) hit the same lookup, as do `draft.py:176` and `draft_namespace.py:60`.

**Repro:** `e2e` Playwright run with `/team/lineup` and `/team/waiver` mocked to the backend's real 404. UI matches what was reported.

**Fix direction:** On import, identify the user's team and set `owner_user_id` and `LeagueMember.host_team_id`. ESPN: match the SWID against `teams[].owners`. Yahoo: use the `is_owned_by_current_login` flag. Sleeper: match `roster.owner_id` to the user's Sleeper id. Then re-import existing leagues (backfill).

## BUG-2: ESPN roster snapshot shape is incompatible with the lineup optimizer — FIXED (ESPN and Yahoo; detail moved to `snapshot.entries`)

`espn_service.py:229` stores `snapshot["players"]` as a list of dicts (`espn_id`, `sleeper_id`, ...). `team.py:208` treats `snapshot["players"]` as a list of Sleeper player ID strings. Even with BUG-1 fixed, ESPN lineups would be wrong or crash. `starters` mixes Sleeper IDs and raw ESPN IDs when mapping fails (`espn_service.py:227`).

## BUG-3: TeamPage header and dead roster code — FIXED (header uses the active league's team name; dead code removed)

`TeamPage.tsx` calls `/team/my` and reads `team_name`, `record`, `points_for`, `roster`, but the endpoint returns only `{leagues, user_id}`. The header is always "Team Manager" and the `roster` / `PlayerCard` code is unused. The only player UI is `LineupCard`, which depends on `/team/lineup` (BUG-1).

## BUG-4: TeamPage lineup query omits `league_id` — FIXED

`TeamPage.tsx:143` calls `/team/lineup` without `league_id`, which FastAPI rejects with 422 in production. The e2e mocks use a wildcard route and hide this. It feeds the compare pool in the player drawer, so comparing players silently has no data.

## BUG-5: `/users/me` and `/notifications` return 500 in the test environment

Seen on every page load (mocked environment, no backend running, so may be the dev proxy only). Needs confirmation against a real backend.

## BUG-6: Stale ESPN e2e tests — FIXED

`e2e/tests/uat-7-espn-connect.spec.ts:49` and `:57` fail: "Private league" no longer reveals the SWID, espn_s2 and League ID inputs (the extension connect flow replaced them, PRs #36-#40). Tests need updating.

## BUG-7: e2e suite is brittle or out of date

- `uat-6-arq-worker.spec.ts` (4 tests) needs Docker/backend, so it fails locally.
- `uat-10-draft-room.spec.ts` SC-5 and DR-10 are flaky timing assertions (505 ms against a 500 ms limit, 462 ms against 200 ms).

## Not verified

The real deployed site (predictfantasyfootball.com) was not driven because it needs your login. All findings come from the code plus mocked API responses. Confirming BUG-1 against production data means checking the `teams.owner_user_id` column for your league.

## BUG-8: Roster lookups only matched the exact current week — FIXED

ESPN and Yahoo imports hardcode `week=1`, but `/team/lineup`, `/team/waiver` and `/team/standings` filtered on `Roster.week == <current NFL week>`. After BUG-1 this would have produced "Roster snapshot not found". They now use the newest snapshot at or before the current week (`_latest_roster` in `team.py`).

## BUG-9: Standings only list teams owned by connected users (open)

`team.py` standings joins `LeagueMember.user_id == Team.owner_user_id`, so an ESPN or Yahoo league shows only your own team until other members connect. Needs a design decision (show all teams in the league, with owner unknown).

## Deploy and verification

Existing leagues need a re-connect after deploy to backfill ownership (the import is idempotent). Sleeper leagues need a re-import through the UI so the Sleeper user id is sent.
