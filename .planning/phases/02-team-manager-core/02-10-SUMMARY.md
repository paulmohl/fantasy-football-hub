---
phase: 02-team-manager-core
plan: "10"
subsystem: ui
tags: [react, react-query, radix-ui, zustand, waiver-wire, faab, dialog]

dependency_graph:
  requires:
    - phase: 02-07
      provides: frontend/src/store/league.ts — useLeagueStore with activeLeagueId
    - phase: 02-09
      provides: frontend/src/components/InjuryBadge.tsx — used in WaiverCard player rows
    - phase: 02-06
      provides: backend/app/api/v1/team.py — GET /team/waiver route with waiver_type, mode, players, drop_suggestions, faab_bid
  provides:
    - frontend/src/components/WaiverCard.tsx — ranked waiver wire list with dual-mode toggle
    - frontend/src/components/AddPlayerDialog.tsx — add player dialog with FAAB bid and drop candidates
  affects:
    - Plan 11 (PlayerDetailDrawer) — TeamPage card stack now includes WaiverCard between LineupCard and StandingsCard

tech-stack:
  added: []
  patterns:
    - queryKey includes mode so React Query re-fetches automatically on mode toggle (DECISION-003)
    - WaiverCard passes drop_suggestions and faab_bid from API response to AddPlayerDialog via onAddPlayer callback
    - AddPlayerDialog is a read-only stub in Phase 2; handleAdd() is a timed no-op (Phase 3+ will POST to /team/waiver/add)
    - Radix DropdownMenu.Item disabled prop + title for off-season tooltip (no separate tooltip component needed)

key-files:
  created:
    - frontend/src/components/WaiverCard.tsx
    - frontend/src/components/AddPlayerDialog.tsx
  modified:
    - frontend/src/pages/TeamPage.tsx

key-decisions:
  - "WaiverPlayer interface exported from WaiverCard.tsx so TeamPage can type AddPlayerState.player without duplication"
  - "onAddPlayer callback signature extended to include drop_suggestions and faab_bid — passes API response data directly rather than re-fetching in dialog"
  - "AddPlayerDialog DropCandidate and FaabBid interfaces duplicated in TeamPage rather than exported from AddPlayerDialog — avoids circular import and keeps dialog self-contained"
  - "Build errors (vite.config.ts path/dirname, selectedPlayer unknown type) are pre-existing from Plan 09 — out of scope per deviation rule scope boundary"

requirements-completed:
  - TM-05
  - TM-06
  - TM-07
  - TM-12

duration: ~2min
completed: "2026-06-27"
---

# Phase 02 Plan 10: WaiverCard and AddPlayerDialog

**Ranked waiver wire card with Trend-weighted/Full composite dual-mode toggle, paginated player list, and AddPlayerDialog with FAAB bid recommendation and selectable drop candidates**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-27T11:35:03Z
- **Completed:** 2026-06-27T11:37:12Z
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `WaiverCard` fetches GET /team/waiver with `mode` in queryKey — React Query re-fetches automatically on mode toggle
- Mode dropdown via Radix DropdownMenu: "Trend-weighted" and "Full composite"; off-season disables items with "In-season data only" title
- Player rows: rank number, name + InjuryBadge, position/team, active-mode score (toFixed(1)), Add (+) button with aria-label
- Pagination: 10 rows initially, "Show 20 more" increments visibleCount by 20
- Loading skeleton (10 animated rows), error state with retry link, empty state for zero players
- `AddPlayerDialog` FAAB section: suggested range chip ($mid ± $range) + numeric input; shown only when `waiverType === 'faab'`
- `AddPlayerDialog` rolling section: "Priority #N" read-only text; shown only when `waiverType === 'rolling'`
- Drop candidates: 1–3 selectable player cards with `border-accent bg-accent/10` selected state; footer button label changes to "Add X, Drop Y"
- TeamPage: WaiverCard replaces placeholder div; AddPlayerDialog rendered with `open={!!addPlayer}` state

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create WaiverCard with dual-mode toggle | 9da2913 | frontend/src/components/WaiverCard.tsx |
| 2 | Create AddPlayerDialog and wire WaiverCard into TeamPage | c59d000 | frontend/src/components/AddPlayerDialog.tsx, frontend/src/pages/TeamPage.tsx |

## Files Created/Modified

- `frontend/src/components/WaiverCard.tsx` — WaiverPlayer/DropSuggestion/FaabBid/WaiverResponse types; dual-mode queryKey; pagination state; InjuryBadge integration; onAddPlayer passes drop_suggestions + faab_bid from response
- `frontend/src/components/AddPlayerDialog.tsx` — Radix Dialog; FAAB bid section (conditional on waiver_type); rolling priority section (conditional); drop candidate selection with accent highlight; read-only stub handleAdd
- `frontend/src/pages/TeamPage.tsx` — Added WaiverCard + AddPlayerDialog imports; AddPlayerState interface; addPlayer useState; WaiverCard replaces placeholder; AddPlayerDialog with open/onClose/playerName/waiverType/dropCandidates/faabBid props

## Decisions Made

**WaiverPlayer exported from WaiverCard:** TeamPage needs to type `AddPlayerState.player`. Exporting from WaiverCard avoids a separate types file and duplication.

**onAddPlayer callback passes API data:** The callback signature is `(player, waiverType, dropCandidates, faabBid)` so the dialog receives everything it needs from the single waiver API fetch — no second request needed when opening the dialog.

**Read-only stub handleAdd:** Phase 2 is explicitly read-only per plan threat model (T-02-10-01). handleAdd() fakes a 500ms delay then closes. Phase 3+ will replace this with a real POST call.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written, with one minor enhancement:

**1. [Rule 2 - Missing Critical] Extended onAddPlayer callback to pass drop_suggestions and faab_bid**
- **Found during:** Task 1 (WaiverCard creation)
- **Issue:** Plan's original onAddPlayer signature was `(player, waiverType)`. AddPlayerDialog in Task 2 requires `dropCandidates` and `faabBid` data from the waiver API response. If not passed through the callback, the dialog would have no data to show for its core FAAB/drop-candidate functionality.
- **Fix:** Extended callback to `(player, waiverType, dropCandidates, faabBid)` — passes the API response data directly through. AddPlayerState in TeamPage mirrors this shape.
- **Files modified:** frontend/src/components/WaiverCard.tsx, frontend/src/pages/TeamPage.tsx
- **Committed in:** 9da2913 (Task 1), c59d000 (Task 2)

---

**Total deviations:** 1 auto-extended (Rule 2 — missing data flow for dialog's core functionality)
**Impact on plan:** Necessary for correctness — without drop_suggestions and faab_bid reaching AddPlayerDialog, the FAAB section and drop candidates would always render empty.

## Issues Encountered

**Pre-existing build errors (out of scope):**
- `vite.config.ts` — `Cannot find module 'path'` and `Cannot find name '__dirname'` — pre-existing from Phase 0 scaffold
- `TeamPage.tsx` line 151 — `Type 'unknown' is not assignable to type 'ReactNode'` — pre-existing from Plan 09 (selectedPlayer typed as `unknown` pending Plan 11's PlayerDetailDrawer)

Both confirmed pre-existing via `git stash` + build check before this plan's changes. Logged to deferred-items.

## Known Stubs

- `frontend/src/components/AddPlayerDialog.tsx` handleAdd(): timed no-op; Phase 3+ will call POST /api/v1/team/waiver/add
- `frontend/src/pages/TeamPage.tsx` line 151-153: `selectedPlayer && <div />` — PlayerDetailDrawer wired in Plan 11

## Threat Flags

None — WaiverCard is read-only (GET only). AddPlayerDialog submit is an explicit Phase 2 stub with no server writes. T-02-10-01 and T-02-10-02 both have `accept` disposition per plan threat model.

## Next Phase Readiness

- WaiverCard and AddPlayerDialog complete; TeamPage card stack is LineupCard → WaiverCard → StandingsCard
- Plan 11 (PlayerDetailDrawer) can slot in without touching WaiverCard or AddPlayerDialog
- Phase 3+: AddPlayerDialog.handleAdd() ready to be replaced with POST /api/v1/team/waiver/add

## Self-Check: PASSED

Files created:
- frontend/src/components/WaiverCard.tsx: EXISTS
- frontend/src/components/AddPlayerDialog.tsx: EXISTS
- frontend/src/pages/TeamPage.tsx: EXISTS (modified)

Commits:
- 9da2913: EXISTS (WaiverCard)
- c59d000: EXISTS (AddPlayerDialog + TeamPage)

TypeScript (tsc --noEmit): PASSES (exit 0)

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
