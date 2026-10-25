# Fantasy Hub ESPN Connect (Chromium extension)

Reads the `SWID` and `espn_s2` cookies for espn.com after the user approves, and hands them to the requesting Fantasy Hub page. Nothing is stored; the extension never contacts our backend.

Extension ID (pinned by the manifest `key`): `dmmfcgielmgfnocladkbffflelfidfjl`
Set `VITE_ESPN_EXTENSION_ID=dmmfcgielmgfnocladkbffflelfidfjl` in the frontend build environment.

## Load unpacked
1. `chrome://extensions` -> enable Developer mode -> Load unpacked -> select this folder.
2. Confirm the displayed ID matches the one above.

## Manual checklist
- On the Fantasy Hub page console: `chrome.runtime.sendMessage("dmmfcgielmgfnocladkbffflelfidfjl", {type:"ping"}, console.log)` -> `{installed:true, version:"1.0.0"}`.
- Signed in to espn.com: `{type:"espn.connect"}` -> popup -> Allow -> `{swid, espn_s2}`; Deny -> `{error:"denied"}`.
- Signed out of espn.com: Allow -> `{error:"not_signed_in"}` and the ESPN login tab opens.

## Tests
`npm test` (Node's built-in runner; no dependencies).

## Key
The signing private key is not in the repo. The public `key` in the manifest is what fixes the ID.
