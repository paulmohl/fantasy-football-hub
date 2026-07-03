---
phase: 04-live-draft-room
plan: 07
subsystem: frontend/components/draft
tags: [react, tailwind, zustand, draft-board, snake-draft, pick-clock, bloomberg-terminal]

dependency_graph:
  requires:
    - 04-06 (useDraftStore: picks, config, currentPickNum, pickDeadlineEpoch, isPaused, reactions)
  provides:
    - frontend/src/components/draft/PositionBadge.tsx (colored position pill, text-pos-* tokens)
    - frontend/src/components/draft/PickClock.tsx (server-epoch countdown, 3-state color, progress bar)
    - frontend/src/components/draft/PickCell.tsx (filled/empty/active/my-team/tier-start states)
    - frontend/src/components/draft/DraftBoard.tsx (snake-ordered NxM pick grid)
    - frontend/src/components/draft/DraftRoom.tsx (Bloomberg Terminal 4-column layout shell)
    - frontend/public/sounds/pick.mp3 (placeholder — replace with CC0 before 04-13 E2E)
    - frontend/public/sounds/your-turn.mp3 (placeholder — replace with CC0 before 04-13 E2E)
  affects:
    - 04-08 (QueuePanel, AlertsPanel, BestAvailable — import PositionBadge, wire into DraftRoom col 1/3)
    - 04-09 (RosterPanel, ChatPanel — wire into DraftRoom col 4)
    - 04-10 (PickDrawer — triggered by PickCell onClick; handlePickClick stub is wired in)
    - 04-11 (DraftPage wiring — replaces placeholder cols in DraftRoom with real components)
    - 04-13 (E2E tests — data-testid attributes on all 4 columns + pick cells + sounds)

tech-stack:
  added: []
  patterns:
    - PositionBadge uses text-pos-{position}/bg-pos-{position}/10 custom Tailwind tokens (defined in Phase 1 tailwind.config)
    - PickClock drives countdown from server pickDeadlineEpoch (not local timer) — D-07 server-authoritative pattern
    - DraftBoard derives grid with useMemo on picks/availablePlayers — O(n) lookups for pick_num→DraftPick and player_id→DraftPlayer
    - snakePickToSlot (DraftBoard): 1-based pick_num → [round, teamSlot]; snakeSlot (DraftRoom): 0-based currentPickNum → active slot
    - DraftRoom placeholder columns use data-testid attributes for E2E targeting even before real components are wired

key-files:
  created:
    - frontend/src/components/draft/PositionBadge.tsx
    - frontend/src/components/draft/PickClock.tsx
    - frontend/src/components/draft/PickCell.tsx
    - frontend/src/components/draft/DraftBoard.tsx
    - frontend/src/components/draft/DraftRoom.tsx
    - frontend/public/sounds/pick.mp3
    - frontend/public/sounds/your-turn.mp3

key-decisions:
  - "snakePickToSlot and snakeSlot are two different helpers: snakePickToSlot(pickNum, numTeams) maps 1-based pick to [round, slot] for the board grid; snakeSlot(currentPickNum, numTeams) maps last-completed pick to the on-clock team slot for the header"
  - "handleEmitPick removed from DraftBoard — plan included it but it was unreachable; pick submission will be wired through PickDrawer in plan 04-10"
  - "activeTeamName shows team_id (not team name) — DraftConfig.draft_order is string[] of team IDs with no name field; 04-11 can enrich with team metadata from league store"
  - "Audio files are minimal placeholders (44-byte MPEG frames) — must be replaced with real CC0 audio from freesound.org before 04-13 E2E tests run (OQ4/B7)"

requirements-completed:
  - DR-02
  - DR-05
  - DR-06
  - DR-07
  - DR-11
  - DR-12

duration: 7min
completed: "2026-07-03"
---

# Phase 4 Plan 07: DraftRoom Bloomberg Shell, DraftBoard Snake Grid, PickCell, PickClock, PositionBadge Summary

**Bloomberg Terminal 4-column DraftRoom shell (D-01 LOCKED) with full snake DraftBoard, server-epoch PickClock, tier-aware PickCell, and position-colored PositionBadge — core visual layer for the live draft room**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-07-03T13:35:53Z
- **Completed:** 2026-07-03T13:43:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created PositionBadge with text-pos-qb/rb/wr/te/k/def custom Tailwind tokens; fallback to text-muted/bg-surface for unknown positions
- Created PickClock consuming pickDeadlineEpoch from useDraftStore; text-warning at <=30s, text-danger + animate-pulse at <=10s (D-03 LOCKED); PAUSED display when isPaused=true; progress bar with matching color state
- Created PickCell with 5 visual states (empty/filled/active/my-team/tier-start); data-testid="pick-cell-{N}" for E2E; emoji reactions (max 3 per D-02); AUTO badge for auto-picks
- Created DraftBoard: snake grid via snakePickToSlot (1-based); useMemo for O(n) pick+player lookups; tier boundary detection from player.tier field; column headers with "YOU" accent for my team slot
- Created DraftRoom: grid-cols-[200px_1fr_320px_200px] with min-w-0 on center column; board header with "on the clock" + PickClock; snakeSlot helper for activeTeamName; placeholder columns with data-testid for 04-11 wiring
- Created frontend/public/sounds/ with placeholder pick.mp3 and your-turn.mp3 (needed by DraftPage.tsx audio refs created in 04-06)

## Task Commits

1. **Task 1: PositionBadge, PickClock, PickCell** - `73a0827c` (feat)
2. **Task 2: DraftBoard, DraftRoom** - `784732ff` (feat)

## Files Created/Modified

- `frontend/src/components/draft/PositionBadge.tsx` — Colored position pill with custom Tailwind tokens; 6 positions + fallback
- `frontend/src/components/draft/PickClock.tsx` — Server-epoch countdown; 3-state color (text/warning/danger); progress bar; PAUSED display
- `frontend/src/components/draft/PickCell.tsx` — Pick grid cell; 5 states; reaction badges; AUTO text; tier border; data-testid
- `frontend/src/components/draft/DraftBoard.tsx` — Snake draft board NxM grid; useMemo lookups; tier tracking; column headers
- `frontend/src/components/draft/DraftRoom.tsx` — 4-column Bloomberg shell; board header; placeholder cols 1/3/4 with data-testid
- `frontend/public/sounds/pick.mp3` — Placeholder audio file (44 bytes); must replace with CC0 before 04-13
- `frontend/public/sounds/your-turn.mp3` — Placeholder audio file (44 bytes); must replace with CC0 before 04-13

## Decisions Made

- Two separate snake helpers needed: `snakePickToSlot(pickNum, numTeams)` in DraftBoard maps 1-based pick_num to [round, teamSlot] for grid cell placement; `snakeSlot(currentPickNum, numTeams)` in DraftRoom maps 0-based lastCompleted to on-clock team slot for the header. Different mathematical bases, different purposes.
- `activeTeamName` uses team_id string (from draft_order[]) — no team name field in DraftConfig. Plan code had `?.team_name` which would be TS error on string; using team ID is correct for this plan; 04-11 can enrich display with league store data.
- `handlePickClick` kept as no-op stub in DraftBoard and wired to PickCell.onClick so the prop chain is established. Plan 04-10 replaces the stub body with the PickDrawer open action.
- Audio files are 44-byte MPEG frame placeholders. DraftPage's `.catch(() => {})` means failed play() doesn't break the app. Real CC0 files needed before 04-13 E2E tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused `muteAudio` from PickClock.tsx**
- **Found during:** Task 1 (PickClock implementation)
- **Issue:** Plan code declared `const muteAudio = useDraftStore(...)` but never used it (comment says audio is handled in DraftPage). With `noUnusedLocals: true` in tsconfig.app.json, this is a compile error.
- **Fix:** Removed the muteAudio line. Audio mute logic stays in DraftPage.tsx (already implemented in 04-06).
- **Files modified:** `frontend/src/components/draft/PickClock.tsx`
- **Verification:** 0 TypeScript errors for PickClock.tsx
- **Committed in:** `73a0827c` (Task 1)

**2. [Rule 1 - Bug] Fixed `?.team_name` TypeScript error in DraftRoom.tsx**
- **Found during:** Task 2 (DraftRoom implementation)
- **Issue:** Plan code: `config.draft_order[snakeSlot(...)]?.team_name` — but `draft_order` is `string[]`, so indexing returns `string | undefined`. TypeScript strict mode: "Property 'team_name' does not exist on type 'string'".
- **Fix:** Use the string directly: `config.draft_order[snakeSlot(...)] ?? '—'`. Shows team_id as label; real name lookup deferred to 04-11.
- **Files modified:** `frontend/src/components/draft/DraftRoom.tsx`
- **Verification:** 0 TypeScript errors for DraftRoom.tsx
- **Committed in:** `784732ff` (Task 2)

**3. [Rule 1 - Bug] Fixed `useDraftStore.getState()` in JSX render in DraftRoom.tsx**
- **Found during:** Task 2 (DraftRoom implementation)
- **Issue:** Plan code called `useDraftStore.getState().currentPickNum` directly inside JSX — non-reactive, won't update on state change (stale render).
- **Fix:** Used the already-subscribed `currentPickNum` from `useDraftStore((s) => s.currentPickNum)` for the round display. Extracted to `currentRound` derived variable.
- **Files modified:** `frontend/src/components/draft/DraftRoom.tsx`
- **Verification:** Round display is now reactive; 0 TS errors
- **Committed in:** `784732ff` (Task 2)

**4. [Rule 1 - Bug] Removed unused `getDraftSocket` import + `handleEmitPick` from DraftBoard.tsx**
- **Found during:** Task 2 (DraftBoard implementation)
- **Issue:** Plan code imported `getDraftSocket` from `@/lib/socket` and defined `handleEmitPick` — but `handleEmitPick` was never called from DraftBoard. With `noUnusedLocals: true`, both would be TS errors.
- **Fix:** Removed both. Pick submission is planned for PickDrawer (04-10), not DraftBoard directly. `handlePickClick` no-op stub maintains the PickCell.onClick prop chain.
- **Files modified:** `frontend/src/components/draft/DraftBoard.tsx`
- **Verification:** 0 TypeScript errors for DraftBoard.tsx
- **Committed in:** `784732ff` (Task 2)

---

**Total deviations:** 4 auto-fixed (all Rule 1 — TypeScript correctness)
**Impact on plan:** All fixes required for compilation under strict TypeScript settings. No scope changes. All plan intent preserved.

## Known Stubs

- `handlePickClick` in DraftBoard.tsx: no-op body — plan 04-10 (PickDrawer) will add the open action
- DraftRoom columns 1, 3, 4: "Loading..." placeholder divs — plan 04-11 replaces with QueuePanel, BestAvailable, RosterPanel, ChatPanel
- `activeTeamName` shows team_id not team name — 04-11 can enrich via league store team metadata
- `frontend/public/sounds/pick.mp3` + `your-turn.mp3`: 44-byte MPEG frame placeholders — must be replaced with real CC0 audio (≤100KB, freesound.org) before plan 04-13 E2E tests run

## Threat Surface Scan

No new network endpoints or auth paths introduced. Both components are read-only visual consumers of useDraftStore. Pick submission (socket.emit('pick')) was in the plan's handleEmitPick but was removed (unused); it will be implemented in 04-10 PickDrawer with proper server validation per T-4-01.

## Self-Check: PASSED

- `frontend/src/components/draft/PositionBadge.tsx` exists: FOUND
- `frontend/src/components/draft/PickClock.tsx` exists: FOUND
- `frontend/src/components/draft/PickCell.tsx` exists: FOUND
- `frontend/src/components/draft/DraftBoard.tsx` exists: FOUND
- `frontend/src/components/draft/DraftRoom.tsx` exists: FOUND
- `frontend/public/sounds/pick.mp3` exists: FOUND (44 bytes)
- `frontend/public/sounds/your-turn.mp3` exists: FOUND (44 bytes)
- Task 1 commit `73a0827c` in git log: FOUND
- Task 2 commit `784732ff` in git log: FOUND
- Zero TypeScript errors in all 5 draft/ component files: VERIFIED
- `text-pos-qb` in PositionBadge for QB: VERIFIED
- `remaining <= 30 && remaining > 10` in PickClock: VERIFIED
- `data-testid="pick-cell-{pickNum}"` in PickCell: VERIFIED
- `border-t-2 border-accent` for isTierStart in PickCell: VERIFIED
- `ring-2 ring-accent animate-pulse` for isActive in PickCell: VERIFIED
- `grid grid-cols-[200px_1fr_320px_200px]` in DraftRoom: VERIFIED
- `min-w-0` on center column in DraftRoom: VERIFIED
- `on the clock` string in DraftRoom board header: VERIFIED
- `snakeSlot(` helper function in DraftRoom: VERIFIED
- `activeTeamName` derivation in DraftRoom: VERIFIED
- `gridTemplateColumns: repeat(${numTeams}...)` in DraftBoard: VERIFIED
- `data-testid="queue-alerts-column"` in DraftRoom Col 1: VERIFIED
- `data-testid="draft-board-column"` in DraftRoom Col 2: VERIFIED
- `data-testid="best-available-column"` in DraftRoom Col 3: VERIFIED
- `data-testid="roster-chat-column"` in DraftRoom Col 4: VERIFIED

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-03*
