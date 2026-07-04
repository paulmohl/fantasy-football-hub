---
phase: 04-live-draft-room
plan: 12
subsystem: backend/draft-api, frontend/draft-room
tags: [fastapi, react, draft-room, gap-closure, html2canvas]
dependency_graph:
  requires: [04-11]
  provides: [draft-players-endpoint, draft-recap-component, commissioner-user-id-config]
  affects:
    - backend/app/api/v1/draft.py
    - frontend/src/store/draft.ts
    - frontend/src/pages/DraftPage.tsx
    - frontend/src/components/draft/DraftRecap.tsx
tech_stack:
  added: []
  patterns: [html2canvas-png-export, redis-cache-join, zustand-store-selector]
key_files:
  created:
    - frontend/src/components/draft/DraftRecap.tsx
  modified:
    - backend/app/api/v1/draft.py
    - frontend/src/store/draft.ts
    - frontend/src/pages/DraftPage.tsx
decisions:
  - Team import added to draft.py from app.models.league (was importing League, LeagueMember only)
  - get_draft adds current_user dependency to resolve my_team_id via Team.owner_user_id join
  - get_draft_players placed before update_draft_order to maintain route ordering (/{draft_id}/players avoids UUID collision)
  - DraftRecap playerName uses availablePlayers store (populated by SC-3 player fetch) for name resolution
  - html2canvas scale:2 for 2x resolution PNG export
metrics:
  duration: "12 minutes"
  completed: "2026-07-04"
  tasks: 4
  files: 4
---

# Phase 4 Plan 12: Gap Closure — Player Data + DraftRecap Summary

**One-liner:** Closed two critical gaps — GET /drafts/{id}/players populates BestAvailable with real names, and DraftRecap renders grades/value picks/reaches/pick log with html2canvas PNG export.

## What Was Built

This plan closed the final two gaps from the Phase 4 gap analysis:

1. **GET /drafts/{id} enriched** — `my_team_id` and `commissioner_user_id` now returned. `get_draft` gains `current_user` dependency; queries `Team` by `league_id + owner_user_id` to resolve `my_team_id`. `commissioner_user_id` serialized from `draft.commissioner_user_id`. `Team` import added to draft.py.

2. **GET /drafts/{id}/players** — new endpoint returning enriched player data for the BestAvailable panel. Joins Sleeper player pool (names, positions, NFL teams) from Redis with FantasyCalc redraft rankings (overall_rank). Filters to active QB/RB/WR/TE/K/DEF only. Sorted by overall_rank ascending. Protected by `get_draft_for_user` (T-4-01).

3. **DraftConfig.commissioner_user_id** — field added to the TypeScript interface. setConfig call in DraftPage now includes `commissioner_user_id: data.commissioner_user_id ?? ''`. This unblocks PauseOverlay commissioner gating (stub from 04-11 resolved).

4. **DraftPage player fetch on mount** — after setConfig, DraftPage fires `GET /drafts/{id}/players` and calls `setAvailablePlayers`. Failure is non-critical (IDs shown instead of names). `setAvailablePlayers` selector added to store destructuring.

5. **DraftRecap.tsx** — new component for `status='complete'`. Fetches `GET /drafts/{id}/recap` via useEffect. Renders: team grades table (color-coded A=emerald, B=accent, C=amber, D/F=red), value picks badge list, reaches badge list, full pick log table. Export button uses html2canvas to capture the recap div at 2x scale as PNG. `data-testid="draft-recap"` on container; `data-testid="export-recap-button"` on export button.

6. **DraftPage complete status wired** — `data-testid="draft-recap-placeholder"` div replaced with `<DraftRecap />` import. Gap 4 fully closed.

## Commits

| Task | Hash | Description |
|------|------|-------------|
| 1 | 37036c52 | feat(04-12): add my_team_id and commissioner_user_id to GET /drafts/{id} |
| 2 | d21a5e9c | feat(04-12): add GET /drafts/{id}/players endpoint for BestAvailable panel |
| 3 | a332b0bd | feat(04-12): add commissioner_user_id to DraftConfig; fetch players on DraftPage mount |
| 4 | 46cf1cdd | feat(04-12): create DraftRecap component and wire into DraftPage complete status |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all stubs from 04-11 resolved:
- `commissionerUserId` in PauseOverlay was `null`; now wired from `config.commissioner_user_id`
- Player names in BestAvailable/PickCell were raw IDs; now `availablePlayers` is populated on mount

## Threat Flags

None — GET /drafts/{id}/players is protected by get_draft_for_user (T-4-01 satisfied). commissioner_user_id exposed to all league members is acceptable per plan threat model (UI-gating only).

## Self-Check: PASSED

- `frontend/src/components/draft/DraftRecap.tsx` — FOUND
- `backend/app/api/v1/draft.py` — imports Team, get_draft has current_user, returns my_team_id + commissioner_user_id, get_draft_players route exists
- `frontend/src/store/draft.ts` — DraftConfig includes commissioner_user_id
- `frontend/src/pages/DraftPage.tsx` — setAvailablePlayers selector, /players fetch, DraftRecap import, complete status renders DraftRecap
- `frontend/src/pages/DraftPage.tsx` — no draft-recap-placeholder string (0 matches)
- Commits 37036c52, d21a5e9c, a332b0bd, 46cf1cdd — FOUND
- TypeScript: 0 errors in draft files (19 pre-existing @/lib/utils errors out of scope)
- Backend import: `from app.api.v1.draft import get_draft, get_draft_players` — OK
