---
phase: 04-live-draft-room
plan: 11
subsystem: frontend/draft-room
tags: [react, draft-room, bloomberg-terminal, gap-closure]
dependency_graph:
  requires: [04-05, 04-06, 04-07, 04-08, 04-09, 04-10]
  provides: [bloomberg-terminal-layout-fully-wired]
  affects: [frontend/src/pages/DraftPage.tsx, frontend/src/components/draft/DraftRoom.tsx, frontend/src/components/draft/DraftBoard.tsx, frontend/src/components/draft/PickCell.tsx]
tech_stack:
  added: []
  patterns: [zustand-store-getstate-in-handler, react-usestate-local-ui, right-click-contextmenu-handler]
key_files:
  created:
    - frontend/src/components/draft/PreDraftLobby.tsx
  modified:
    - frontend/src/pages/DraftPage.tsx
    - frontend/src/components/draft/DraftRoom.tsx
    - frontend/src/components/draft/DraftBoard.tsx
    - frontend/src/components/draft/PickCell.tsx
decisions:
  - DraftRoom adds `relative` to outer div className — required for PauseOverlay absolute inset-0 positioning
  - commissionerUserId passed as null to PauseOverlay until plan 04-12 adds commissioner_user_id to DraftConfig
  - PreDraftLobby shows Start Draft button to all users — server enforces commissioner check (T-4-04 mitigated server-side)
  - useAuthStore import removed from PreDraftLobby — unused until 04-12 wires commissioner_user_id
  - DraftBoard internal handlePickClick stub replaced with onPickClick prop — DraftRoom owns PickDrawer state
metrics:
  duration: "9 minutes"
  completed: "2026-07-04"
  tasks: 4
  files: 5
---

# Phase 4 Plan 11: Bloomberg Terminal Assembly Summary

**One-liner:** Full Bloomberg Terminal 4-column draft room assembled — PreDraftLobby created, all panels wired into DraftRoom, PickDrawer state managed, ReactionPicker wired via right-click in PickCell.

## What Was Built

This plan assembled the live draft room layout by closing four gaps:

1. **PreDraftLobby.tsx** — new component for `status='pending'`. Displays draft settings (num_teams, num_rounds, pick_clock_seconds), a draft order list, and a Start Draft button that calls `PUT /drafts/{id}/order` with `lock_and_start: true`. Commissioner gating deferred to plan 04-12.

2. **DraftPage.tsx wired** — both placeholder divs replaced with real component renders: `<PreDraftLobby />` for pending status, `<DraftRoom />` for live/paused status. Complete status placeholder preserved for plan 04-12.

3. **DraftRoom.tsx fully wired** — all five panels (QueuePanel, AlertsPanel, BestAvailable, RosterPanel, ChatPanel) placed in their correct columns. PauseOverlay wired with `commissionerUserId=null` (04-12 will supply the real value). PickDrawer state managed in DraftRoom via `drawerState` / `handlePickClick` / `handleDrawerClose`. Outer div now has `relative` positioning for PauseOverlay's `absolute inset-0`. DraftBoard receives `onPickClick` prop.

4. **PickCell.tsx ReactionPicker** — right-click opens ReactionPicker popover at mouse coordinates. Guard: only fires on filled cells (`if (!pick) return`). Close handlers: outside click and Escape (both handled inside ReactionPicker itself).

5. **DraftBoard.tsx refactored** — internal no-op `handlePickClick` stub removed. Component now accepts `onPickClick?: (pickNum: number) => void` prop, which is passed through to each PickCell.

## Commits

| Task | Hash | Description |
|------|------|-------------|
| 1 | af123e3c | feat(04-11): create PreDraftLobby component for pending draft status |
| 2 | f675ea90 | feat(04-11): wire DraftRoom and PreDraftLobby into DraftPage |
| 3 | 1a2f0e5a | feat(04-11): wire all panels, PauseOverlay and PickDrawer into DraftRoom |
| 4 | 89128d0f | feat(04-11): wire ReactionPicker into PickCell via right-click handler |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused `useAuthStore` import from PreDraftLobby**
- **Found during:** Task 1
- **Issue:** Plan code snippet imported `useAuthStore` but never used it in the component body. TypeScript `noUnusedLocals: true` would have caused a compile error.
- **Fix:** Removed the import. The auth store will be added in 04-12 when `commissioner_user_id` is available for gating the Start Draft button.
- **Files modified:** `frontend/src/components/draft/PreDraftLobby.tsx`
- **Commit:** af123e3c

**2. [Rule 1 - Bug] Removed unused `availablePlayers` store subscription from DraftRoom**
- **Found during:** Task 3
- **Issue:** Plan code snippet subscribed to `availablePlayers` from the draft store but never used the value in the component (PickDrawer handler uses `useDraftStore.getState().picks` directly). TypeScript `noUnusedLocals: true` would have caused a compile error.
- **Fix:** Removed the subscription. The PickDrawer handler uses `useDraftStore.getState()` for the snapshot lookup, which is the correct pattern for event handlers.
- **Files modified:** `frontend/src/components/draft/DraftRoom.tsx`
- **Commit:** 1a2f0e5a

## Known Stubs

- `commissionerUserId` passed to PauseOverlay is always `null` — 04-12 will add `commissioner_user_id` to `DraftConfig` and wire the real value. PauseOverlay renders for all users but commissioner-only controls inside it are already gated on this value.
- PreDraftLobby Start Draft button shown to all users — server validates commissioner role in `update_draft_order` (T-4-04). UI gating deferred to 04-12.

## Threat Flags

None — all security-relevant surfaces match the plan's threat model. `PUT /drafts/{id}/order` already enforces commissioner check server-side (T-4-04 mitigated).

## Self-Check: PASSED

- `frontend/src/components/draft/PreDraftLobby.tsx` — FOUND
- `frontend/src/pages/DraftPage.tsx` — imports DraftRoom and PreDraftLobby, no placeholder divs for pending/live/paused
- `frontend/src/components/draft/DraftRoom.tsx` — 0 "Loading..." strings, all panels imported and rendered
- `frontend/src/components/draft/PickCell.tsx` — ReactionPicker imported, onContextMenu wired
- Commit af123e3c — FOUND
- Commit f675ea90 — FOUND
- Commit 1a2f0e5a — FOUND
- Commit 89128d0f — FOUND
- TypeScript: 0 errors in draft components (19 pre-existing errors in @/lib/utils — out of scope)
