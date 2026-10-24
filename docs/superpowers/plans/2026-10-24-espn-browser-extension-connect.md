# ESPN Browser Extension Connect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a web user connect a private ESPN league by approving a one-time request in a Chromium extension, with credentials stored encrypted and leagues chosen from a list.

**Architecture:** A Manifest V3 extension answers messages from our site (`externally_connectable`), shows an approval popup, reads the `SWID`/`espn_s2` cookies via `chrome.cookies`, and replies to the page. The page then calls the backend (existing `/espn/connect`, new `/espn/leagues`) as the logged-in user. Backend also gets a working credential health check and a date-derived season year.

**Tech Stack:** Chrome MV3 (plain JS, no build), FastAPI + httpx + pytest-asyncio, React 18 + TypeScript + Vite, Vitest (added for the extension wrapper).

**Spec:** `docs/superpowers/specs/2026-10-24-espn-browser-extension-connect-design.md`

## Global Constraints

- Chromium only (Chrome, Edge, Brave, Arc). No Firefox/Safari work.
- Extension never persists cookies and never contacts our backend.
- `externally_connectable.matches` limited to our own origins (`http://localhost:5173/*` plus the production frontend origin).
- Extension ID is stable via a pinned manifest `key`; the frontend reads it from `VITE_ESPN_EXTENSION_ID`.
- Native (Capacitor) ESPN flow unchanged; bookmarklet and manual paste stay behind an "Advanced" link.
- Secrets in `.env`, never hardcoded. No comments that explain what code does. Conventional commits, no emoji.
- Existing `/espn/connect` behaviour and error messages are unchanged.

## Review Focus

- ESPN fan API returns zero football leagues -> UI offers manual League ID entry, not a dead end.
- User not signed in to espn.com (cookies absent) -> clear "sign in to ESPN, then retry" message, ESPN login page opens.
- User closes the approval popup without choosing -> page's pending request resolves as `denied`, button re-enables.
- Two `espn.connect` requests while one popup is open -> second is rejected with `busy`, no second popup.
- `espn_s2` contains `%2B`/`%2F` -> passed through unmodified to the backend and to ESPN.
- Message from an origin not in `externally_connectable` -> Chrome refuses it; extension also checks `sender.origin` against an allowlist.

---

### Task 1: Extension (ping, approval popup, cookie read)

**Files:**
- Create: `extension/manifest.json`, `extension/background.js`, `extension/approve.html`, `extension/approve.js`, `extension/README.md`
- Create: `extension/test/background.test.js`, `extension/package.json` (only `{"type":"module","scripts":{"test":"node --test test/"}}`)

**Interfaces:**
- Produces (message protocol, used by Task 5): request `{type: "ping"}` -> `{installed: true, version: string}`; request `{type: "espn.connect"}` -> `{swid: string, espn_s2: string}` or `{error: "denied" | "not_signed_in" | "busy"}`.
- Produces: `background.js` exports `createHandler({chrome, allowedOrigins}) -> (message, sender) => Promise<object>` so it is testable under `node --test`; the service-worker entry wires it to `chrome.runtime.onMessageExternal`.

- [ ] **Step 1: Write failing tests** in `extension/test/background.test.js` using a fake `chrome` object: `ping` returns `{installed:true, version}`; `espn.connect` with Allow decision and both cookies returns `{swid, espn_s2}` with `espn_s2` containing `%2B` unchanged; Deny returns `{error:"denied"}`; popup window closed with no decision returns `{error:"denied"}`; missing `espn_s2` returns `{error:"not_signed_in"}` and calls `chrome.tabs.create` with the ESPN login URL; second concurrent `espn.connect` returns `{error:"busy"}`; sender origin not in `allowedOrigins` returns `{error:"forbidden"}`.
- [ ] **Step 2: Run** `cd extension && npm test` -> FAIL (module missing).
- [ ] **Step 3: Implement `background.js` and `approve.{html,js}`.** Popup opened with `chrome.windows.create({url: approve.html?origin=...})`; decision passed back via `chrome.runtime.sendMessage({type:"approval", allow})`; `chrome.windows.onRemoved` resolves as deny. Cookies read with `chrome.cookies.get({url:"https://www.espn.com", name})` for `SWID` and `espn_s2`.
- [ ] **Step 4: Write `manifest.json`:** MV3, permissions `["cookies"]`, `host_permissions: ["https://*.espn.com/*"]`, `externally_connectable.matches` per Global Constraints, `key` generated with `openssl genrsa 2048 | openssl rsa -pubout -outform DER | base64 -w0`. Document in `extension/README.md` how to derive the extension ID from the key and how to load unpacked.
- [ ] **Step 5: Run** `npm test` -> PASS.
- [ ] **Step 6: Manual check** (checklist in README): load unpacked, from the page console on `localhost:5173` run `chrome.runtime.sendMessage("<id>", {type:"ping"}, console.log)` -> `{installed:true,...}`; run `espn.connect` while signed in to espn.com -> popup -> Allow -> cookies logged.
- [ ] **Step 7: Commit** `feat(extension): add ESPN cookie connect extension`.

### Task 2: ESPN fan API client + real-login spike

**Files:**
- Modify: `backend/app/services/espn_client.py`
- Create: `backend/tests/fixtures/espn_fan.json` (captured in Step 1)
- Modify: `backend/tests/test_espn_client.py`

**Interfaces:**
- Produces: `ESPNClient.get_fan_leagues(self, swid: str) -> list[dict]` returning `[{"league_id": str, "name": str, "season": int}]` for football (`ffl`) entries only; raises `ESPNAuthExpired` on 401/403. Used by Tasks 3 and 4.

- [ ] **Step 1: Spike (needs Paul).** With the Task 1 extension, Paul copies his own `SWID`/`espn_s2` and runs `curl -H "Cookie: SWID=...; espn_s2=..." "https://fan.api.espn.com/apis/v2/fans/{SWID}?displayEvents=false&displayHiddenPrefs=true&context=fantasy&source=fan_api_fantasy&useCookies=true&lang=en"`. Save the response with names/ids scrubbed to `backend/tests/fixtures/espn_fan.json`. If the response has no usable league list, stop and revise the spec (manual League ID fallback becomes the primary path).
- [ ] **Step 2: Write failing tests** in `test_espn_client.py`: `test_get_fan_leagues_parses_football_only` (fixture in, expected list out), `test_get_fan_leagues_empty`, `test_get_fan_leagues_401_raises_auth_expired`. Use the same httpx mocking style as the existing tests in that file.
- [ ] **Step 3: Run** `cd backend && pytest tests/test_espn_client.py -v` -> new tests FAIL.
- [ ] **Step 4: Implement `get_fan_leagues`**, sending cookies the same way `get_league` does. Parse against the fixture shape.
- [ ] **Step 5: Run** the same command -> PASS.
- [ ] **Step 6: Commit** `feat(espn): add fan API league discovery`.

### Task 3: `POST /espn/leagues`

**Files:**
- Modify: `backend/app/api/v1/espn.py`, `backend/tests/test_espn_routes.py`

**Interfaces:**
- Consumes: `ESPNClient.get_fan_leagues` (Task 2).
- Produces: `POST /v1/espn/leagues` body `{swid: str, espn_s2: str}` -> `{"leagues": [{"league_id": str, "name": str, "season": int}]}`; 401 with the existing "ESPN cookies are expired or invalid…" detail on `ESPNAuthExpired`. Auth, rate limit, and test mocking follow `/espn/connect`.

- [ ] **Step 1: Write failing tests:** `test_espn_leagues_returns_list`, `test_espn_leagues_expired_cookies_401`, `test_espn_leagues_requires_auth` (mirror `test_espn_connect_invalid_cookies`).
- [ ] **Step 2: Run** `pytest tests/test_espn_routes.py -k leagues -v` -> FAIL.
- [ ] **Step 3: Implement** `ESPNLeaguesRequest` and `espn_list_leagues` in `espn.py`.
- [ ] **Step 4: Run** -> PASS; run full `tests/test_espn_routes.py` -> PASS.
- [ ] **Step 5: Commit** `feat(espn): add leagues discovery endpoint`.

### Task 4: Credential health check and season year

**Files:**
- Modify: `backend/workers/tasks.py` (ESPN branch, ~line 150-165), `backend/app/api/v1/espn.py` (`credential_dict` in `/espn/connect`), `backend/app/core/config.py:83`
- Test: `backend/tests/test_espn_health.py` (new), `backend/tests/test_season_year.py` (new)

**Interfaces:**
- Consumes: `ESPNClient.get_fan_leagues`.
- Produces: `settings.nfl_season_year` derives from today's date (calendar year if month >= 3, else year - 1) unless `NFL_SEASON_YEAR` is set. `/espn/connect` also stores `league_id` in the credential dict.

- [ ] **Step 1: Write failing tests:** health check marks a private ESPN credential unhealthy when `get_fan_leagues` raises `ESPNAuthExpired`, leaves it healthy on success, and no longer calls `get_league_settings` with the SWID as league ID; season year is 2025 on 2026-02-15, 2026 on 2026-10-24 (inject the date), and the env override wins.
- [ ] **Step 2: Run** `pytest tests/test_espn_health.py tests/test_season_year.py -v` -> FAIL.
- [ ] **Step 3: Implement:** replace the ESPN branch of the health check to call `get_fan_leagues(decrypted["swid"])`; add `league_id` to `credential_dict`; add a `model_validator`/default factory on `Settings.nfl_season_year`.
- [ ] **Step 4: Run** the new tests plus `pytest tests/test_credential_service.py tests/test_espn_routes.py` -> PASS.
- [ ] **Step 5: Commit** `fix(espn): working credential health check and derived season year`.

### Task 5: Frontend extension wrapper

**Files:**
- Create: `frontend/src/lib/espnExtension.ts`, `frontend/src/lib/espnExtension.test.ts`
- Modify: `frontend/package.json` (add `vitest` dev dependency and `"test": "vitest run"`), `frontend/vite.config.ts` (test env `node`), `.env.example` (`VITE_ESPN_EXTENSION_ID=`)

**Interfaces:**
- Consumes: message protocol from Task 1.
- Produces: `isInstalled(): Promise<boolean>`; `requestCookies(): Promise<{swid: string; espn_s2: string}>` which rejects with `EspnExtensionError` whose `code` is `"not_installed" | "denied" | "not_signed_in" | "busy" | "unreachable"`.

- [ ] **Step 1: Write failing tests** with `globalThis.chrome` mocked: `isInstalled` true on ping reply, false when `chrome` undefined, false when `lastError` set; `requestCookies` resolves with cookies and passes `espn_s2` through unmodified; rejects with each error code mapped from the reply; rejects `unreachable` when `lastError` is set after the extension was detected.
- [ ] **Step 2: Run** `cd frontend && npm install && npm test` -> FAIL.
- [ ] **Step 3: Implement** `espnExtension.ts` using `chrome.runtime.sendMessage(import.meta.env.VITE_ESPN_EXTENSION_ID, msg, cb)` with a 2s ping timeout.
- [ ] **Step 4: Run** `npm test` and `npm run type-check` -> PASS.
- [ ] **Step 5: Commit** `feat(frontend): add ESPN extension messaging wrapper`.

### Task 6: Connect screen

**Files:**
- Modify: `frontend/src/pages/ConnectPage.tsx` (the `espn_private` step, ~lines 418-560, plus new state/handlers near line 135-280)
- Test: `frontend/src/pages/ConnectPage.espn.test.tsx` (add `@testing-library/react`, `jsdom`)

**Interfaces:**
- Consumes: `isInstalled`, `requestCookies`, `EspnExtensionError` (Task 5); `POST /espn/leagues` and `POST /espn/connect` (Tasks 3, existing).
- Produces: web ESPN step states `not_installed` -> `ready` -> `waiting` -> `pick_league`; `?reconnect=espn` on `/connect` jumps straight to `ready`. Native branch and the bookmarklet/manual form are untouched and reachable via an "Advanced" link.

- [ ] **Step 1: Write failing tests** (extension wrapper and `api` mocked): not-installed state shows install button and "Check again" re-pings; Connect click -> leagues listed -> selecting one posts `/espn/connect` with the cookies and the chosen `league_id`; zero leagues shows the manual League ID input; `denied` and `not_signed_in` show their messages and re-enable the button; `?reconnect=espn` starts in `ready`; native (`isNative()` true) still renders the "Sign in to ESPN" button.
- [ ] **Step 2: Run** `npm test` -> FAIL.
- [ ] **Step 3: Implement** the states in `ConnectPage.tsx`, reusing the existing Tailwind patterns, `espnError`, and `handleEspnPrivateSubmit` for the final connect call (parameterize it with the picked league ID).
- [ ] **Step 4: Run** `npm test`, `npm run type-check`, `npm run lint` -> PASS.
- [ ] **Step 5: Manual end-to-end** with the unpacked extension and local backend: sign in to ESPN, Connect, Allow, pick league, see "connected"; then log out of ESPN and confirm the not-signed-in message.
- [ ] **Step 6: Commit** `feat(frontend): extension-based ESPN connect flow`.
