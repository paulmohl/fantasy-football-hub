---
phase: 02-team-manager-core
plan: "09"
subsystem: ui
tags: [react, dnd-kit, react-query, zustand, lineup, badges, injury]

dependency_graph:
  requires:
    - phase: 02-07
      provides: frontend/src/store/league.ts — useLeagueStore with activeLeagueId and weekOverrides
    - phase: 02-08
      provides: frontend/src/components/StandingsCard.tsx — ready to slot into TeamPage card stack
    - phase: 02-06
      provides: backend/app/api/v1/team.py — GET /team/lineup route
  provides:
    - frontend/src/components/LineupCard.tsx — two-column current/optimal lineup with dnd-kit drag override
    - frontend/src/components/InjuryBadge.tsx — inline injury status badge with Q/D/OUT/IR/SUSP/PUP tiers
    - frontend/src/components/ConfidenceBadge.tsx — confidence score pill with success/warning/danger tiers
  affects:
    - Plan 10 (WaiverCard) — slots into same TeamPage card stack
    - Plan 11 (PlayerDetailDrawer) — selectedPlayer state wired and ready, onPlayerClick passed to LineupCard

tech-stack:
  added: []
  patterns:
    - dnd-kit DndContext + SortableContext + useSortable wraps Optimal column only (Current column is read-only)
    - Drag handle opacity-0 group-hover:opacity-100 with min-w-[44px] touch target
    - weekOverrides from useLeagueStore written on drag end via setOverride(week, slot, player_id)
    - NoStrongCallBanner replaces FLEX row when no_strong_call=true (role=alert, AlertTriangle icon)
    - Pure display component pattern for badges: props-in, badge-out, null for unrecognized status

key-files:
  created:
    - frontend/src/components/InjuryBadge.tsx
    - frontend/src/components/ConfidenceBadge.tsx
    - frontend/src/components/LineupCard.tsx
  modified:
    - frontend/src/pages/TeamPage.tsx

key-decisions:
  - "clearOverrides called from destructured store (not getState()) — consistent with how setOverride is already destructured"
  - "selectedPlayer state typed as unknown in TeamPage — PlayerDetailDrawer shape not yet defined (Plan 11 will add the type)"
  - "CLAUDE.md preference: all explanatory comments removed from badge and card components"

requirements-completed:
  - TM-01
  - TM-02
  - TM-04
  - TM-10
  - TM-15

duration: ~10min
completed: "2026-06-27"
---

# Phase 02 Plan 09: LineupCard, InjuryBadge, ConfidenceBadge

**Two-column current/optimal lineup card with dnd-kit drag reorder, InjuryBadge Q/D/OUT/IR tier system, ConfidenceBadge success/warning/danger tiers, NoStrongCallBanner for FLEX slot, and SWAP badges on divergent current starters**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-06-27
- **Tasks:** 2
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments

- `InjuryBadge` maps Q/D/OUT/IR/SUSP/PUP/NA to warning/danger tier colors; returns null for null/undefined/Active/unrecognized
- `ConfidenceBadge` renders score pill with success (>=70), warning (55-69), danger (<55) tiers; font-mono
- `LineupCard` two-column grid: Current (read-only `CurrentPlayerRow`) | Optimal (draggable `DraggablePlayerRow`)
- SWAP badge (`bg-accent text-white`) on current-column rows where `is_swap_suggested=true`
- `NoStrongCallBanner` replaces FLEX slot in Optimal column when `no_strong_call=true`; `role="alert"` for screen readers
- dnd-kit `DndContext` wraps Optimal column only; drag end writes `setOverride(week, slot, player_id)` to Zustand
- Projected total row: `currentTotal → +delta pts` with `text-success`/`text-danger` delta color; optimal shown right-aligned
- "Clear overrides" button appears when `weekOverrides[week]` has entries
- `TeamPage` wires `<LineupCard onPlayerClick={setSelectedPlayer} />` and `<StandingsCard />`, replacing all placeholders
- `selectedPlayer` state ready for `PlayerDetailDrawer` (Plan 11)
- TypeScript compiles clean (`npx tsc --noEmit` exit 0)

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create InjuryBadge and ConfidenceBadge primitives | 30a7d54 | frontend/src/components/InjuryBadge.tsx, frontend/src/components/ConfidenceBadge.tsx |
| 2 | Create LineupCard and wire StandingsCard into TeamPage | ce1c198 | frontend/src/components/LineupCard.tsx, frontend/src/pages/TeamPage.tsx |

## Files Created/Modified

- `frontend/src/components/InjuryBadge.tsx` — Pure display component: INJURY_CONFIG maps 7 statuses to label+className; returns null for null/unknown
- `frontend/src/components/ConfidenceBadge.tsx` — Pure display component: confidenceTierClass() returns success/warning/danger Tailwind classes
- `frontend/src/components/LineupCard.tsx` — Main lineup card: SlotData/LineupResponse types, NoStrongCallBanner, CurrentPlayerRow, DraggablePlayerRow, LineupCard with DndContext
- `frontend/src/pages/TeamPage.tsx` — Replaced LineupCard and StandingsCard placeholders; added selectedPlayer state for Plan 11

## Decisions Made

**selectedPlayer typed as unknown:** PlayerDetailDrawer's exact prop shape is defined in Plan 11. Using `unknown` rather than `any` keeps TypeScript strict without prematurely fixing the type.

**clearOverrides from destructured store:** The plan's code block used `useLeagueStore.getState().clearOverrides(data.week)` in an onClick. Since `clearOverrides` is already destructured at the top of the component, using it directly is cleaner and consistent with how `setOverride` is used elsewhere in the same component.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused `arrayMove` import from LineupCard**
- **Found during:** Task 2 (LineupCard creation)
- **Issue:** The plan's code block imported `arrayMove` from `@dnd-kit/sortable` but the component stores overrides via Zustand rather than reordering a local array. The import would cause a TS6133 unused import error.
- **Fix:** Removed `arrayMove` from the import. Override behavior writes to `weekOverrides` via `setOverride`, which is the correct TM-15 pattern.
- **Committed in:** ce1c198

**2. [Rule 2 - Missing Critical] Added `font-mono` to InjuryBadge**
- **Found during:** Task 1 (InjuryBadge creation)
- **Issue:** Plan acceptance criteria explicitly required `font-mono` on both badge components. The plan's code block for InjuryBadge was missing it (ConfidenceBadge had it).
- **Fix:** Added `font-mono` to InjuryBadge className string.
- **Committed in:** 30a7d54

---

**Total deviations:** 2 auto-fixed (1 Rule 1 bug, 1 Rule 2 missing)
**Impact on plan:** Both trivial fixes for correctness. No scope changes.

## Known Stubs

- `frontend/src/pages/TeamPage.tsx` line 114: WaiverCard placeholder (`bg-surface border...` div) — replaced in Plan 10
- `frontend/src/pages/TeamPage.tsx` line 127-129: `selectedPlayer && <div />` — PlayerDetailDrawer wired in Plan 11

## Threat Flags

None — LineupCard is a pure display component. Drag overrides are client-side only (weekOverrides in localStorage). No server writes triggered by drag events. T-02-09-01 and T-02-09-02 both have `accept` disposition per plan threat model.

## Self-Check: PASSED

Files created:
- frontend/src/components/InjuryBadge.tsx: EXISTS
- frontend/src/components/ConfidenceBadge.tsx: EXISTS
- frontend/src/components/LineupCard.tsx: EXISTS
- frontend/src/pages/TeamPage.tsx: EXISTS (modified)

Commits:
- 30a7d54: EXISTS (InjuryBadge + ConfidenceBadge)
- ce1c198: EXISTS (LineupCard + TeamPage)

TypeScript: PASSES (exit 0)

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
