---
phase: 02-team-manager-core
plan: "07"
subsystem: ui
tags: [zustand, react-query, radix-ui, league-store, team-page, league-switcher, persist]

dependency_graph:
  requires:
    - phase: 02-06
      provides: backend/app/api/v1/team.py — /team/my and all team routes
  provides:
    - frontend/src/store/league.ts — Zustand persisted store for activeLeagueId and weekOverrides
    - frontend/src/components/LeagueSwitcher.tsx — dropdown switcher for multi-league users
    - frontend/src/pages/TeamPage.tsx — extended with card stack layout, league store wiring, skeleton loading
  affects:
    - Wave 5 plans (LineupCard, Plan 09) — imports useLeagueStore + slots into TeamPage card stack
    - Wave 6 plans (WaiverCard, Plan 10) — imports useLeagueStore + slots into TeamPage card stack
    - All future components that need activeLeagueId in their React Query keys

tech-stack:
  added: []
  patterns:
    - Zustand persist middleware with named localStorage key (ffhub-league)
    - activeLeagueId in React Query key to prevent stale cache on league switch
    - LeagueSwitcher returns null for single-league users (zero render cost)
    - Radix DropdownMenu for accessible league context switching
    - Card stack placeholder pattern — placeholders replaced by named plans (self-documenting)

key-files:
  created:
    - frontend/src/store/league.ts
    - frontend/src/components/LeagueSwitcher.tsx
  modified:
    - frontend/src/pages/TeamPage.tsx

key-decisions:
  - "PlayerCard exported (not local) so Wave 5 plans can import it from TeamPage without re-declaring"
  - "Pre-existing vite.config.ts tsc -b errors logged to deferred-items.md — not caused by Plan 07 changes; npx tsc --noEmit passes cleanly"
  - "LeagueSwitcher queries /team/my for leagues array (same endpoint as TeamPage) to avoid a separate /leagues/mine call until multi-league data shape is finalized"

requirements-completed:
  - TM-01
  - TM-02

duration: ~10min
completed: "2026-06-27"
---

# Phase 02 Plan 07: Frontend League Store and TeamPage Card Shell

**Zustand league store persisted to localStorage + LeagueSwitcher Radix dropdown + TeamPage restructured as card stack with skeleton loading and activeLeagueId-scoped React Query key**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-06-27
- **Tasks:** 2
- **Files modified:** 3 (created league.ts, LeagueSwitcher.tsx; rewrote TeamPage.tsx)

## Accomplishments

- `useLeagueStore` with `activeLeagueId`, `weekOverrides`, and 4 actions persisted to `localStorage` under key `ffhub-league`
- `LeagueSwitcher` dropdown: Radix DropdownMenu, renders null for single-league users, active item has `border-l-2 border-accent`, Sleeper SLP badge
- `TeamPage` restructured: page header row (team name + LeagueSwitcher), 3-card skeleton loading, "Select a league" empty state, card stack placeholder with inline comments pointing to replacement plans
- `activeLeagueId` in React Query key `['my-team', activeLeagueId]` — cache invalidates automatically on league switch
- `PlayerCard` exported for reuse by LineupCard (Plan 09) without re-declaration

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create league.ts Zustand store | c6bd8de | frontend/src/store/league.ts |
| 2 | Create LeagueSwitcher and extend TeamPage | 897d6eb | frontend/src/components/LeagueSwitcher.tsx, frontend/src/pages/TeamPage.tsx, .planning/phases/02-team-manager-core/deferred-items.md |

## Files Created/Modified

- `frontend/src/store/league.ts` — Zustand persist store: activeLeagueId, weekOverrides, 4 actions, localStorage key 'ffhub-league'
- `frontend/src/components/LeagueSwitcher.tsx` — Radix dropdown for multi-league context switching; returns null for single-league users
- `frontend/src/pages/TeamPage.tsx` — Extended with store integration, card stack layout, skeleton loading, "Select a league" empty state; PlayerCard kept and exported

## Decisions Made

**PlayerCard exported:** The plan says "keep all existing logic." The new TeamPage layout doesn't render PlayerCard directly (it will be used by LineupCard in Plan 09). Exporting it avoids the `TS6133: 'PlayerCard' is declared but its value is never read` compiler error while keeping the component available for Wave 5.

**LeagueSwitcher data source:** The component queries `/team/my` (same as TeamPage) rather than a separate `/leagues/mine` endpoint. The `leagues` array in the `/team/my` response includes all connected leagues. This avoids an extra round trip and matches the data shape built in Plan 06.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Exported PlayerCard to prevent TS6133 compiler error**
- **Found during:** Task 2 (TeamPage restructure)
- **Issue:** New card stack layout doesn't render PlayerCard inline — Wave 5 plan will render it inside LineupCard. tsc-b flagged it as unused, breaking `npm run build`.
- **Fix:** Changed `function PlayerCard` to `export function PlayerCard` so it's consumed externally
- **Files modified:** frontend/src/pages/TeamPage.tsx
- **Verification:** `npx tsc --noEmit` passes; `npm run build` no longer emits TS6133
- **Committed in:** 897d6eb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing export for reuse)
**Impact on plan:** Fix is necessary for build correctness and Wave 5 consumption. No scope creep.

## Issues Encountered

**Pre-existing vite.config.ts build errors (out of scope):** `npm run build` fails with `TS2307: Cannot find module 'path'` and `TS2304: Cannot find name '__dirname'` in vite.config.ts. These originate from Phase 0 scaffold — `tsconfig.node.json` lacks `@types/node`. Not caused by Plan 07. Logged to `.planning/phases/02-team-manager-core/deferred-items.md`. The app-only TypeScript check (`npx tsc --noEmit`) passes cleanly.

## Known Stubs

- `frontend/src/pages/TeamPage.tsx` line 114: LineupCard placeholder (`bg-surface border...` div) — replaced in Plan 09 (LineupCard)
- `frontend/src/pages/TeamPage.tsx` line 120: WaiverCard placeholder — replaced in Plan 10 (WaiverCard)

These stubs are intentional per the plan's card stack design. They render visible UI (no empty state) and are clearly labeled with replacement plan numbers.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. Frontend localStorage access is per the accepted threat model (T-02-07-01, T-02-07-02): weekOverrides and activeLeagueId are UI-only preferences; server enforces get_league_for_user isolation on every request.

## Next Phase Readiness

- `useLeagueStore` is ready for import by all Wave 5/6 components
- TeamPage card stack has two named placeholder slots ready for LineupCard (Plan 09) and WaiverCard (Plan 10)
- `PlayerCard` exported from TeamPage — LineupCard can import and wrap it with dnd-kit
- `activeLeagueId` flows correctly through React Query keys — league switch triggers re-fetch

## Self-Check: PASSED

Files created:
- frontend/src/store/league.ts: EXISTS
- frontend/src/components/LeagueSwitcher.tsx: EXISTS
- frontend/src/pages/TeamPage.tsx: EXISTS (modified)

Commits:
- c6bd8de: EXISTS (league.ts store)
- 897d6eb: EXISTS (LeagueSwitcher + TeamPage)

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
