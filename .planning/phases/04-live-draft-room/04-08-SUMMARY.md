---
phase: 04-live-draft-room
plan: 08
subsystem: frontend/components/draft
tags: [react, tailwind, zustand, dnd-kit, best-available, queue-panel, tier-dividers, snake-draft]

dependency_graph:
  requires:
    - 04-06 (useDraftStore: availablePlayers, queuedPlayerIds, addToQueue, removeFromQueue, reorderQueue, config, currentPickNum)
    - 04-07 (PositionBadge — imported by both new components)
  provides:
    - frontend/src/components/draft/BestAvailable.tsx (scrollable ranked player list with tier dividers, ADP grades, FROM YOUR QUEUE section, position filter, debounced search)
    - frontend/src/components/draft/QueuePanel.tsx (drag-to-reorder personal pick queue with @dnd-kit/sortable, auto-pick footer hint)
  affects:
    - 04-09 (RosterPanel, ChatPanel — complete the DraftRoom column 4 wiring)
    - 04-11 (DraftPage wiring — replaces col 1 Loading... with QueuePanel, col 3 Loading... with BestAvailable)
    - 04-13 (E2E tests — data-testid attributes available-player-{id} and queue-item-{id})

tech-stack:
  added: []
  patterns:
    - BestAvailable: rawSearch/search two-state debounce (rawSearch=immediate input display, search=debounced filter, 150ms)
    - BestAvailable: isOnTheClock via snake-order activeTeamSlot derivation (consistent with DraftRoom.snakeSlot helper)
    - QueuePanel: optimistic-then-sync pattern (reorderQueue store action first, then socket.emit)
    - QueuePanel: @dnd-kit/sortable verticalListSortingStrategy with PointerSensor + KeyboardSensor (accessibility)
    - Both: getDraftSocket() for socket emission; null-check before emit

key-files:
  created:
    - frontend/src/components/draft/BestAvailable.tsx
    - frontend/src/components/draft/QueuePanel.tsx

decisions:
  - "rawSearch state variable drives input value display (immediate); search state drives filter (debounced 150ms) — fixes noUnusedLocals error from plan code that used value={search} while declaring rawSearch"
  - "Unicode escape sequences used for special chars (checkmark, X, braille dots) to avoid ESLint/encoding issues in JSX"
  - "activeTeamSlot derivation in BestAvailable uses same snake math as DraftRoom.snakeSlot but 1-based (currentPickNum+1) — produces identical results"

metrics:
  duration: "~6 min"
  completed: "2026-07-03"
  tasks_completed: 2
  files_changed: 2
---

# Phase 4 Plan 08: BestAvailable and QueuePanel Summary

**BestAvailable ranked player list (tier dividers, ADP grades, FROM YOUR QUEUE section, position filter, 150ms debounced search) and QueuePanel drag-to-reorder queue (@dnd-kit/sortable, optimistic-then-server-sync) — complete selection workflow for the live draft room**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-03T13:52:42Z
- **Completed:** 2026-07-03T13:58:xx Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- BestAvailable panel with position filter tabs (ALL/QB/RB/WR/TE/K/DEF), 150ms debounced search (rawSearch/search two-state), tier dividers on tier boundary changes (D-11), ADP grade color badges (A+=emerald-400 through F=red-400), FROM YOUR QUEUE top-3 section when isOnTheClock (D-09), and queue +Q button calling addToQueue + socket.emit('queue_add')
- Drafted players rendered with opacity-40 + line-through on name for tier context maintenance (D-10 LOCKED)
- QueuePanel with DndContext + SortableContext + verticalListSortingStrategy; SortableQueueItem with drag handle, rank, PositionBadge, name/team, remove button; handleDragEnd uses arrayMove + optimistic reorderQueue + socket.emit('queue_reorder')
- Auto-pick footer hint: "Auto-pick: {first queued player}" (D-09: top = auto-draft fallback on clock expiry)
- Both panels: data-testid attributes for E2E test targeting

## Task Commits

1. **Task 1: BestAvailable panel** - `31723650` (feat)
2. **Task 2: QueuePanel drag-to-reorder** - `aea9c9a5` (feat)

## Files Created/Modified

- `frontend/src/components/draft/BestAvailable.tsx` — position filter, debounced search, FROM YOUR QUEUE, tier dividers, ADP grade badges, drafted=dim+strikethrough, queue-add button
- `frontend/src/components/draft/QueuePanel.tsx` — @dnd-kit/sortable drag-to-reorder, optimistic update + server sync, remove button, auto-pick footer

## Decisions Made

- `rawSearch` drives input `value` (immediate display); `search` drives filtering (debounced 150ms) — plan code had `value={search}` which would make `rawSearch` unused (noUnusedLocals error) and cause the input to lag 150ms behind user typing (bad UX)
- Unicode escapes used for special characters (&#10003; for checkmark, &#10005; for X, &#10271; for drag handle) — avoids potential encoding issues in JSX string literals
- `isOnTheClock` derives activeTeamSlot using `currentPickNum + 1` (next pick, 1-based) — consistent with DraftRoom's `snakeSlot(currentPickNum, numTeams)` (0-based last-completed); both produce same on-clock slot

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed rawSearch unused variable — input value used debounced state causing lag**
- **Found during:** Task 1 (BestAvailable analysis pre-write)
- **Issue:** Plan code declared `const [rawSearch, setRawSearch] = useState('')` but used `value={search}` on the input. This means: (a) `rawSearch` is written to but never read — TypeScript `noUnusedLocals: true` would reject it; (b) the input would show the debounced value, causing 150ms lag in user's typed characters (broken UX).
- **Fix:** Changed input `value` from `{search}` to `{rawSearch}`. Now rawSearch is the controlled input value (immediate display) and search is the debounced filter value. Both states are read. Input responds instantly; filtering delays 150ms.
- **Files modified:** `frontend/src/components/draft/BestAvailable.tsx`
- **Commit:** `31723650`

## Known Stubs

None — both panels wire to live useDraftStore data. When `availablePlayers` and `queuedPlayerIds` are populated by DraftPage socket handlers (04-06), both components render real data.

## Threat Surface Scan

No new network endpoints or auth paths. Both components are client-side only and emit via existing authenticated socket (T-4-02 and T-4-05 from plan threat model are accepted — server validates queue adds at pick time via Redis SISMEMBER; queue order is user preference only).

## Self-Check: PASSED

- `frontend/src/components/draft/BestAvailable.tsx` exists: FOUND
- `frontend/src/components/draft/QueuePanel.tsx` exists: FOUND
- Task 1 commit `31723650` in git log: FOUND
- Task 2 commit `aea9c9a5` in git log: FOUND
- 0 TypeScript errors from new files (19 pre-existing @/lib/utils errors unchanged): VERIFIED
- `'FROM YOUR QUEUE'` string in BestAvailable.tsx: VERIFIED
- `debounceRef` + `setTimeout` with `150` in BestAvailable.tsx: VERIFIED
- `value={rawSearch}` on search input (not {search}): VERIFIED
- `setSearch` inside `setTimeout` in onChange: VERIFIED
- `opacity-40` on drafted players: VERIFIED
- `line-through` on drafted player names: VERIFIED
- `SortableContext` import from @dnd-kit/sortable: VERIFIED
- `arrayMove` in handleDragEnd: VERIFIED
- `socket.emit('queue_reorder')` in handleDragEnd: VERIFIED
- `socket.emit('queue_remove')` in handleRemove: VERIFIED
- `data-testid="available-player-{player_id}"` on each player row: VERIFIED
- `data-testid="queue-item-{player_id}"` on each queue item: VERIFIED
- Auto-pick footer with first queued player name: VERIFIED

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-03*
