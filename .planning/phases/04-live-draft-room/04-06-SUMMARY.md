---
phase: 04-live-draft-room
plan: 06
subsystem: frontend/store + frontend/lib + frontend/pages
tags: [zustand, socket.io-client, draft-store, draft-page, trade-stub, event-replay, audio]

dependency_graph:
  requires:
    - 04-03 (draft_service: record_draft_event, replay_since for backend replay)
    - 04-04 (draft_namespace: Socket.IO /draft event shapes — pick_confirmed, auto_drafted, draft_paused, draft_resuming, replay_event)
    - 04-05 (REST API: GET /drafts/{draft_id} for initial config fetch)
  provides:
    - frontend/src/store/draft.ts (useDraftStore — all draft client state)
    - frontend/src/lib/socket.ts (connectDraftSocket/getDraftSocket/disconnectDraftSocket)
    - frontend/src/pages/DraftPage.tsx (status-routing shell; placeholder divs for 04-11)
    - frontend/src/pages/TradePage.tsx (stub satisfying App.tsx import)
  affects:
    - 04-07+ (Wave 5 components import useDraftStore and connectDraftSocket)
    - 04-11 (PreDraftLobby, DraftRoom, DraftRecap replace placeholder divs in DraftPage)

tech-stack:
  added:
    - frontend/src/vite-env.d.ts (vite/client type reference for import.meta.env)
  patterns:
    - useDraftStore follows auth.ts/league.ts Zustand persist pattern; persist name 'draft-storage'
    - partialize excludes all volatile fields (picks, config, deadlines) — only lastEventId, muteAudio, queuedPlayerIds persisted
    - addPick marks isDrafted:true in-place (not filter/remove) per D-10
    - socket.ts module-level singleton pattern: _socket variable, connectDraftSocket replaces on re-call
    - DraftPage useEffect cleanup: socket.off() all handlers + disconnectDraftSocket()
    - replay_event flat-field extraction (Redis stream values are strings; Number() coercion for pick_num/round)

key-files:
  created:
    - frontend/src/store/draft.ts
    - frontend/src/lib/socket.ts
    - frontend/src/pages/DraftPage.tsx
    - frontend/src/pages/TradePage.tsx
    - frontend/src/vite-env.d.ts

decisions:
  - "ReplayEventData interface adds player_id/team_id/round/is_auto_pick as string fields — Redis XRANGE streams all values as strings; Number() coercion at use site"
  - "DraftPage exports both named (export function DraftPage) and default (export default DraftPage) — plan specifies named; App.tsx requires default"
  - "api named import { api } used in DraftPage — api.ts has no default export (hardcoded baseURL /api/v1)"
  - "vite-env.d.ts added as Rule 3 fix — socket.ts import.meta.env.VITE_API_URL requires Vite type reference absent from project"
  - "muteAudio captured as closure in useEffect([draftId, token]) — stale if user toggles mute between reconnects; acceptable for stub phase; Wave 5 components can read store directly"

metrics:
  duration: "~9 min"
  completed: "2026-07-03"
  tasks_completed: 2
  files_changed: 5
---

# Phase 4 Plan 06: Zustand Draft Store, Socket.IO Client, DraftPage Shell, TradePage Stub Summary

**Zustand draft store with partitioned persistence, Socket.IO /draft namespace client, DraftPage event-handler shell routing on draft.status, and TradePage stub — complete client-side state/connection foundation for Wave 5 components**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-03T13:16:38Z
- **Completed:** 2026-07-03T13:26:10Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created useDraftStore with 13 actions, correct partialize (only 3 fields persisted), addPick with in-place isDrafted marking (D-10), and functional updater for setResumeCountdown (D-05)
- Built connectDraftSocket factory connecting to /draft namespace at /ws path with auth dict; module-level singleton with graceful re-connect replacement
- DraftPage registers 9 socket event handlers: pick_confirmed, auto_drafted, pick_deadline_sync, draft_paused, draft_resuming, draft_complete, chat_message, reaction_added, replay_event
- replay_event switch covers all 6 event types; flat string field extraction for Redis XRANGE replay (D-07 LOCKED)
- D-05 countdown: draft_resuming sets countdown; interval ticks down; setPaused(false) only when reaches 0
- D-06 audio: pick.mp3 on all picks; your-turn.mp3 on-clock only via snake-order calculation
- TradePage stub satisfies App.tsx import with "Trade Center — coming soon" render

## Task Commits

1. **Task 1: Zustand draft store (draft.ts)** - `719080b4` (feat)
2. **Task 2: socket.ts + DraftPage + TradePage + vite-env.d.ts** - `4060bad3` (feat)

## Files Created/Modified

- `frontend/src/store/draft.ts` — useDraftStore: DraftPick/DraftPlayer/DraftConfig/DraftState interfaces; 13 actions; persist partialize for lastEventId/muteAudio/queuedPlayerIds only
- `frontend/src/lib/socket.ts` — connectDraftSocket/getDraftSocket/disconnectDraftSocket; singleton _socket; /draft namespace at /ws path; reconnection config (10 attempts, 1s-5s delay)
- `frontend/src/pages/DraftPage.tsx` — status-routing shell: loading/error/pending/complete/live+paused placeholders; full socket event handling; audio refs; reconnect emit on connect
- `frontend/src/pages/TradePage.tsx` — stub: "Trade Center — coming soon"
- `frontend/src/vite-env.d.ts` — vite/client type reference (Rule 3 fix for import.meta.env)

## Decisions Made

- `ReplayEventData` interface defines flat string fields (player_id, team_id, round, is_auto_pick, pick_num as string) — Redis XRANGE returns all stream field values as strings; plan code used untyped access which TypeScript strict mode rejects
- Both named and default export added to DraftPage and TradePage — plan acceptance criteria specifies named exports; actual App.tsx uses default imports (needed both)
- `import { api } from '@/lib/api'` — api.ts exports named const, no default export; plan's `import api from '@/lib/api'` would fail
- vite-env.d.ts added — standard Vite project setup file absent from worktree; required for import.meta.env type safety

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added vite-env.d.ts for import.meta.env TypeScript support**
- **Found during:** Task 2 (TypeScript check)
- **Issue:** `socket.ts` uses `import.meta.env.VITE_API_URL` but `frontend/src/vite-env.d.ts` was missing from the worktree. TypeScript error: "Property 'env' does not exist on type 'ImportMeta'" (TS2339).
- **Fix:** Created `frontend/src/vite-env.d.ts` with `/// <reference types="vite/client" />` — standard Vite project boilerplate.
- **Files modified:** `frontend/src/vite-env.d.ts` (created)
- **Commit:** `4060bad3`

**2. [Rule 1 - Bug] Fixed ReplayEventData type — flat Redis stream fields missing from plan type**
- **Found during:** Task 2 (TypeScript analysis)
- **Issue:** Plan's `replay_event` handler typed as `{ id: string; type: string; pick?: DraftPick; ... }` but then accessed `data.player_id`, `data.team_id`, `data.round`, `data.is_auto_pick` — fields not in the type. TypeScript strict mode rejects property access on undefined type members.
- **Fix:** Defined `ReplayEventData` interface with explicit string fields for Redis stream flat values. Used `Number()` coercion at use site for pick_num and round.
- **Files modified:** `frontend/src/pages/DraftPage.tsx`
- **Commit:** `4060bad3`

**3. [Rule 1 - Bug] Fixed api import — plan used default import, api.ts has no default export**
- **Found during:** Task 2 (TypeScript analysis)
- **Issue:** Plan's DraftPage shows `import api from '@/lib/api'` but `api.ts` exports `export const api` (named export, no default). Would fail TypeScript.
- **Fix:** Changed to `import { api } from '@/lib/api'`.
- **Files modified:** `frontend/src/pages/DraftPage.tsx`
- **Commit:** `4060bad3`

**4. [Rule 1 - Bug] Added default exports to DraftPage and TradePage**
- **Found during:** Task 2 (reading App.tsx)
- **Issue:** App.tsx uses `import DraftPage from '@/pages/DraftPage'` and `import TradePage from '@/pages/TradePage'` (default imports), but plan specifies named exports only. Missing default export would cause runtime import failure.
- **Fix:** Added `export default DraftPage` and `export default TradePage` after the named export functions.
- **Files modified:** `frontend/src/pages/DraftPage.tsx`, `frontend/src/pages/TradePage.tsx`
- **Commit:** `4060bad3`

## Known Stubs

- `DraftPage.tsx` placeholder divs (PRE-DRAFT LOBBY, DRAFT ROOM, DRAFT RECAP) — these are intentional per plan; Plan 04-11 replaces them with PreDraftLobby, DraftRoom, DraftRecap components
- `TradePage.tsx` "Trade Center — coming soon" — intentional stub; full implementation deferred to Phase 5 per plan
- `useDraftStore.getState().currentPickNum + 1` in DRAFT ROOM placeholder JSX — reads state directly (not reactive); acceptable since 04-11 will replace this div
- `muteAudio` in useEffect closure — stale if user toggles between reconnects; Wave 5 DraftRoom component can use `useDraftStore.getState().muteAudio` directly for real-time accuracy

## Threat Surface Scan

No new network endpoints or auth paths introduced beyond what the plan's threat model covers.

| Aspect | Assessment |
|--------|-----------|
| T-4-01 (auth token in socket) | token from useAuthStore (server-issued JWT) forwarded in auth dict; server validates in on_connect |
| T-4-03 (event handler tampering) | All store mutations triggered by server-emitted events; client cannot construct picks directly |

## Pre-existing Issues (Out of Scope)

- `@/lib/utils` missing module errors across 20+ existing components — pre-existing, not caused by this plan; logged to deferred items
- `frontend/package-lock.json` modified by npm install run during TypeScript verification — not committed; worktree-local state change

## Self-Check: PASSED

- `frontend/src/store/draft.ts` exists: FOUND
- `frontend/src/lib/socket.ts` exists: FOUND
- `frontend/src/pages/DraftPage.tsx` exists: FOUND
- `frontend/src/pages/TradePage.tsx` exists: FOUND
- `frontend/src/vite-env.d.ts` exists: FOUND
- Task 1 commit `719080b4` in git log: FOUND
- Task 2 commit `4060bad3` in git log: FOUND
- Zero TypeScript errors for all four new plan files: VERIFIED
- `partialize` includes only lastEventId/muteAudio/queuedPlayerIds: VERIFIED
- `name: 'draft-storage'` in persist config: VERIFIED
- `connectDraftSocket` exports verified: VERIFIED
- `socket.on('auto_drafted')` handler calls `addPick` and `setPickDeadline`: VERIFIED
- `replay_event` switch includes `pick_confirmed` and `auto_drafted` cases: VERIFIED
- `pickSoundRef.current?.play()` present (D-06): VERIFIED
- `your-turn.mp3` present (D-06 on-clock audio): VERIFIED
- `setResumeCountdown` in draft_resuming handler (D-05): VERIFIED
- `useRef` imported in DraftPage: VERIFIED

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-03*
