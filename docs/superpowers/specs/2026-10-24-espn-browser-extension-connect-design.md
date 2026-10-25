# ESPN Browser Extension Connect — Design

## Goal
Replace the ESPN bookmarklet / manual cookie paste on web with a one-time, user-approved connection. The user clicks "Connect ESPN", approves in a browser extension, and the app stores their ESPN credentials (encrypted) and reads their leagues. Chromium browsers only (Chrome, Edge, Brave, Arc). Native (Capacitor) keeps its existing flow.

## Background
ESPN has no OAuth for fantasy. Private leagues need the `SWID` and `espn_s2` cookies for espn.com, which a web page on our origin cannot read. An extension with host permission can read them via `chrome.cookies`, including HttpOnly cookies.

## Approach (chosen: externally_connectable messaging)
1. Page calls `chrome.runtime.sendMessage(EXTENSION_ID, msg)`.
2. Extension shows an approval popup naming the requesting origin.
3. On Allow, extension reads `SWID` and `espn_s2` and replies to the page.
4. Page calls backend as the logged-in user; backend validates, stores encrypted, imports.

Rejected: content-script + postMessage (more moving parts, spoofable by page scripts); extension POSTing directly to backend (needs token handoff, new auth surface).

## Components

### 1. Extension (`extension/`, Manifest V3, no build step)
- `manifest.json`: permissions `cookies`; `host_permissions` `https://*.espn.com/*`; `externally_connectable.matches` limited to prod and dev origins; pinned `key` so the extension ID is stable.
- `background.js` handles messages from the page:
  - `ping` -> `{installed: true, version}`
  - `espn.connect` -> open approval popup, wait for decision.
    - Allow: read cookies. Missing either cookie -> `{error: "not_signed_in"}` and open the ESPN login page.
    - Deny -> `{error: "denied"}`.
    - Success -> `{swid, espn_s2}`.
- `approve.html` / `approve.js`: "Fantasy Hub wants to read your ESPN fantasy leagues", requesting origin shown, Allow / Deny.
- Never persists cookies; never contacts our backend.

### 2. Frontend
- `frontend/src/lib/espnExtension.ts`: wrapper (`isInstalled()`, `requestCookies()`), maps `chrome.runtime.lastError` and error codes to typed errors.
- `ConnectPage.tsx` ESPN private step (web) has three states:
  - Not installed: install button (Web Store link; load-unpacked instructions in dev) and "Check again".
  - Ready: "Connect ESPN" button -> "Waiting for approval…".
  - Connected: league picker (from `/espn/leagues`), then import.
- Bookmarklet and manual paste move behind an "Advanced" link. Native flow unchanged.
- `/connect?reconnect=espn` (from `HealthBanner`) runs the same flow.

### 3. Backend
- New `POST /espn/leagues` `{swid, espn_s2}` -> list of the user's football leagues via ESPN's fan API. Fallback if the fan API is unusable: user enters league ID manually (existing field).
- `/espn/connect` unchanged in behaviour.
- Store `swid` and `espn_s2` (and `league_id` where known) so the health check can work.
- Fix `workers/tasks.py` credential health check: it reads `league_id` from the credential (never stored) and falls back to the SWID as league ID, so expired cookies are never detected. Use a league-independent check.
- Replace hard-coded `nfl_season_year = 2025` with a date-derived value (override still possible via env).

### 4. Errors
- Extension: not installed, denied, not signed in to ESPN, extension unreachable.
- Backend: ESPN rejecting cookies -> 401 with the existing ESPN-specific message; league not found -> 404.
- App login token expiry handled by the interceptor change in `frontend/src/lib/api.ts` (refresh and retry on app-auth 401s for platform routes).

## Testing
- Backend: pytest for `/espn/leagues` (ESPN mocked) and the fixed health check.
- Frontend: unit tests for `espnExtension.ts` with `chrome.runtime` mocked.
- Extension: manual checklist, loaded unpacked in Chrome.
- First spike (before building UI): verify against a real ESPN login that `chrome.cookies` returns both cookies and that the fan API returns the league list.

## Out of scope
Firefox/Safari, mobile extension flows, Chrome Web Store submission (dev uses load-unpacked), any flow that handles the user's ESPN password.
