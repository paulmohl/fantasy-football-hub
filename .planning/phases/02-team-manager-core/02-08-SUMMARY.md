---
phase: 02-team-manager-core
plan: "08"
subsystem: ui
tags: [react-query, zustand, standings, league-store]

dependency_graph:
  requires:
    - phase: 02-06
      provides: backend/app/api/v1/team.py — GET /team/standings route
    - phase: 02-07
      provides: frontend/src/store/league.ts — useLeagueStore with activeLeagueId
  provides:
    - frontend/src/components/StandingsCard.tsx — League standings card ready for TeamPage slot
  affects:
    - Wave 5 plans — StandingsCard slots into TeamPage card stack alongside LineupCard and WaiverCard

tech-stack:
  added: []
  patterns:
    - React Query queryKey includes activeLeagueId (Pitfall 6 compliant) to prevent stale cache on league switch
    - Div-row standings table (no HTML table element) per UI-SPEC Surface J
    - cn() conditional class application for current user row elevation

key-files:
  created:
    - frontend/src/components/StandingsCard.tsx
  modified: []

key-decisions:
  - "Removed code comments that explain what code does (per CLAUDE.md preference) — implementation matches plan spec exactly"

requirements-completed:
  - TM-07

duration: ~2min
completed: "2026-06-27"
---

# Phase 02 Plan 08: StandingsCard Component

**League standings card with React Query, current-user row elevation, 8-row skeleton, and error/empty states — ready to plug into TeamPage Wave 5 card stack**

## Performance

- **Duration:** ~2 min
- **Completed:** 2026-06-27
- **Tasks:** 1
- **Files modified:** 1 (created StandingsCard.tsx)

## Accomplishments

- `StandingsCard` component fetches from `GET /api/v1/team/standings` with `queryKey: ['team-standings', activeLeagueId]`
- Current user row visually elevated: `bg-raised border border-border` on the row + `font-semibold` on team name
- Each row shows rank (1-based index), team name, record (W-L), and pts_for (.toFixed(1))
- Loading state: 8-row `animate-pulse bg-raised rounded-lg` skeleton
- Empty state: "Standings unavailable" heading + explanatory subtext
- Error state: "Couldn't load standings." with reload button
- Week indicator footer: "Through week N" shown when data present
- TypeScript compiles without errors (`npx tsc --noEmit` clean)

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create StandingsCard component | bb01dc5 | frontend/src/components/StandingsCard.tsx |

## Files Created/Modified

- `frontend/src/components/StandingsCard.tsx` — League standings card: useQuery with activeLeagueId key, current user row elevation, 8-row skeleton, empty/error states, week indicator

## Decisions Made

**Comments removed:** Per CLAUDE.md ("No comments explaining what code does — only explain non-obvious why"), the plan's code block included several UI-SPEC reference comments (e.g., `{/* Loading: 8-row skeleton (UI-SPEC Surface J) */}`). These were removed as they describe what the code does rather than why.

## Deviations from Plan

None — plan executed exactly as written (minus explanatory comments per CLAUDE.md preference).

## Known Stubs

None — StandingsCard is a complete, production-ready component. It has no hardcoded data; all content comes from the `/team/standings` API response.

## Threat Flags

None — StandingsCard is a pure read display component. No writes, no new auth paths, no schema changes. The only network call is `GET /team/standings` which the server already isolates via `get_league_for_user` (T-02-08-01: accept disposition confirmed in plan threat model).

## Self-Check: PASSED

Files created:
- frontend/src/components/StandingsCard.tsx: EXISTS

Commits:
- bb01dc5: EXISTS (StandingsCard component)

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
