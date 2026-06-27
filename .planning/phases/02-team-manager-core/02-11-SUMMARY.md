---
phase: 02-team-manager-core
plan: "11"
subsystem: ui
tags: [react, react-query, radix-ui, recharts, drawer, player-detail, compare, weather, trendchart]

dependency_graph:
  requires:
    - phase: 02-09
      provides: frontend/src/components/InjuryBadge.tsx, ConfidenceBadge.tsx — used in PlayerDetailDrawer and PlayerComparePanel
    - phase: 02-10
      provides: frontend/src/components/WaiverCard.tsx — WaiverPlayer type used in TeamPage AddPlayerState
    - phase: 02-07
      provides: frontend/src/store/league.ts — activeLeagueId used in useQuery keys
  provides:
    - frontend/src/components/PlayerDetailDrawer.tsx — Full TM-03 player detail panel with Radix Dialog, real stats, NL explanation
    - frontend/src/components/PlayerComparePanel.tsx — TM-08 head-to-head comparison calling /team/trade API
    - frontend/src/components/WeatherChip.tsx — Inline and full-size weather alert chip
    - frontend/src/components/TrendChart.tsx — Recharts LineChart weekly points trend
    - frontend/src/pages/TeamPage.tsx (modified) — PlayerDetailDrawer wired with comparePool and selectedPlayer as PlayerSlotData
  affects:
    - Plan 12 (player-stats backend route) — PlayerDetailDrawer calls GET /team/stats/{player_id}?league_id={id}; Plan 12 adds the backend
    - Phase 3+ — PlayerSlotData interface may need matchup_grade/opponent_rank_vs_position populated from lineup API

tech-stack:
  added:
    - recharts@3.9.0 (was in package.json but not installed; npm install recharts run as Rule 3 fix)
  patterns:
    - PlayerSlotData exported from PlayerDetailDrawer.tsx — union-compatible interface for both LineupCard.SlotData and WaiverPlayer
    - Radix Dialog with bottom-sheet mobile / right-panel desktop via Tailwind sm: breakpoint classes
    - comparePool built via useQuery with same key as LineupCard (React Query deduplication, no extra fetch)
    - onPlayerClick adapter in TeamPage converts SlotData to PlayerSlotData (null player_id guard)
    - Recharts Tooltip formatter typed with typeof v === 'number' guard (Recharts v3 ValueType may be undefined)

key-files:
  created:
    - frontend/src/components/WeatherChip.tsx
    - frontend/src/components/TrendChart.tsx
    - frontend/src/components/PlayerDetailDrawer.tsx
    - frontend/src/components/PlayerComparePanel.tsx
  modified:
    - frontend/src/pages/TeamPage.tsx

key-decisions:
  - "comparePool built in TeamPage via separate useQuery with same ['team-lineup', activeLeagueId] key — React Query deduplicates the request so no extra API call; LineupCard and TeamPage share the cached response"
  - "PlayerSlotData exported from PlayerDetailDrawer.tsx to avoid circular imports — LineupCard.SlotData mapped to PlayerSlotData in TeamPage via adapter closure"
  - "Recharts Tooltip formatter typed defensively with typeof v === 'number' guard — Recharts v3 changed ValueType to include undefined"
  - "onSelectPlayerB(null as unknown as PlayerSlotData) pattern used in Change button — acceptable cast since parent immediately re-nulls state; alternative would require separate onClearPlayerB prop"

requirements-completed:
  - TM-03
  - TM-08
  - TM-09
  - TM-13

duration: ~6min
completed: "2026-06-27"
---

# Phase 02 Plan 11: PlayerDetailDrawer, WeatherChip, TrendChart, PlayerComparePanel

**Radix Dialog drawer with TM-03 full player analysis (matchup_grade, opponent_rank_vs_position, recent_usage_trend, 3-sentence NL explanation, real Recharts trend chart via useQuery) and TM-08 head-to-head PlayerComparePanel with /team/trade API and three_biggest_factors**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-27T11:39:56Z
- **Completed:** 2026-06-27T11:46:00Z
- **Tasks:** 2
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments

- `WeatherChip` returns null for indoor stadiums and below-threshold conditions; WMO codes 71-77 for snow, >=63 or >=2.5mm for heavy rain; WIND_THRESHOLD=20mph; compact/full size variants
- `TrendChart` uses Recharts LineChart with #3DA9FC stroke, dot=false, isLoading skeleton, empty-state for off-season; no CartesianGrid; custom styled Tooltip
- `PlayerDetailDrawer` Radix Dialog: bottom sheet on mobile (85vh), right panel on desktop (max-w-[400px]); ESC closes via Dialog.Root onOpenChange; aria-label="Close player details" on X button
- `PlayerDetailDrawer` TM-03 fields: matchup_grade chip with GRADE_COLOR map (A=success, B=success/5, C=text, D=warning, F=danger), opponent_rank_vs_position as #N, recent_usage_trend via TREND_LABEL
- `PlayerDetailDrawer` TM-13 real stats: useQuery(['player-stats', player_id, leagueId]) calls GET /team/stats/{player_id}; no dummyTrendData anywhere in codebase
- `buildNLExplanation` 3-sentence NL: s1=start/sit recommendation by confidence tier, s2=top factor (injury/matchup grade), s3=usage trend or weather context
- `PlayerComparePanel` TM-08: playerB selection from comparePool list when no playerB selected; useQuery(['trade', playerA.player_id, playerB.player_id, leagueId]) calls GET /team/trade; winner column border-success/30 bg-success/5
- `PlayerComparePanel` renders point_delta, confidence, and up to 3 biggest_factors (label + detail)
- `TeamPage` selectedPlayer now typed as `PlayerSlotData | null`; comparePool built from lineup useQuery (React Query cache hit, no extra fetch); LineupCard onPlayerClick adapter maps SlotData to PlayerSlotData

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create WeatherChip and TrendChart primitives | 45df8fa | frontend/src/components/WeatherChip.tsx, frontend/src/components/TrendChart.tsx |
| 2 | Create PlayerDetailDrawer, PlayerComparePanel, wire into TeamPage | a298e0b | frontend/src/components/PlayerDetailDrawer.tsx, frontend/src/components/PlayerComparePanel.tsx, frontend/src/pages/TeamPage.tsx, frontend/src/components/TrendChart.tsx |

## Files Created/Modified

- `frontend/src/components/WeatherChip.tsx` — compact/full variants; null for indoor or no weather alert; Wind/CloudRain/CloudSnow icons from lucide-react; WIND_THRESHOLD=20, WMO snow 71-77, heavy rain >=63 or >=2.5mm
- `frontend/src/components/TrendChart.tsx` — Recharts ResponsiveContainer/LineChart; #3DA9FC stroke; dot=false; isLoading pulse skeleton; empty-state "Stats available in-season"; Tooltip with custom contentStyle
- `frontend/src/components/PlayerDetailDrawer.tsx` — Radix Dialog; exports PlayerSlotData; buildNLExplanation 3-sentence; GRADE_COLOR/TREND_LABEL; useQuery player-stats; Compare button opens PlayerComparePanel; weatherChip full-size in drawer
- `frontend/src/components/PlayerComparePanel.tsx` — imports PlayerSlotData from PlayerDetailDrawer; useQuery /team/trade; playerB selection list from comparePool; winner highlight; three_biggest_factors list; point_delta + confidence
- `frontend/src/pages/TeamPage.tsx` — added PlayerDetailDrawer import; selectedPlayer typed as PlayerSlotData; LineupSlot/LineupData interfaces; lineup useQuery for comparePool; LineupCard onPlayerClick adapter; PlayerDetailDrawer rendered with all props

## Decisions Made

**comparePool via useQuery in TeamPage:** The lineup data needed for playerB selection is loaded inside LineupCard via `['team-lineup', activeLeagueId]`. Rather than lifting lineup state or adding a callback prop to LineupCard, TeamPage issues the same useQuery — React Query deduplicates the fetch from cache. This keeps LineupCard self-contained.

**PlayerSlotData adapter in TeamPage onPlayerClick:** LineupCard's internal `SlotData` has `player_id: string | null` and `slot: string`. TeamPage's `onPlayerClick` adapter guards against null player_id and maps fields explicitly. Avoids exporting SlotData from LineupCard or creating a shared types file.

**Recharts v3 Tooltip type fix:** Recharts upgraded ValueType to include `undefined` in v3 — the plan's code block used `v: number` which fails tsc -b. Fixed by `typeof v === 'number'` guard with string fallback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed recharts (was in package.json but not in node_modules)**
- **Found during:** Task 1 (TrendChart creation)
- **Issue:** `ls node_modules/recharts` returned "not found". package.json listed `"recharts": "^3.9.0"` but npm install had not been run for it. TrendChart import would fail at build time.
- **Fix:** `npm install recharts` from frontend/; installs 71 packages at recharts@3.9.0
- **Files modified:** package-lock.json (tracked but no JSON diff since recharts was already in package.json)
- **Committed in:** 45df8fa (Task 1 commit — package-lock.json had no diff to stage, tracked file unchanged in git)

**2. [Rule 1 - Bug] Fixed Recharts v3 Tooltip formatter type mismatch**
- **Found during:** Task 2 verification (npm run build revealed error TS2322)
- **Issue:** Plan's code block typed the formatter as `(v: number, _: string, item: { payload: WeeklyPoint })` but Recharts v3 changed `ValueType` to include `undefined`, making the parameter incompatible
- **Fix:** Changed to `(v, _name, item) =>` with `typeof v === 'number'` guard; item cast via `(item as { payload: WeeklyPoint })`
- **Files modified:** frontend/src/components/TrendChart.tsx
- **Committed in:** a298e0b (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added api import correction: named {api} not default api**
- **Found during:** Task 2 (PlayerDetailDrawer and PlayerComparePanel creation)
- **Issue:** Plan code blocks used `import api from '@/lib/api'` (default import) but api.ts exports `export const api = ...` (named export). Would fail at runtime.
- **Fix:** All new files use `import { api } from '@/lib/api'` matching existing pattern (confirmed from WaiverCard.tsx)
- **Files modified:** frontend/src/components/PlayerDetailDrawer.tsx, frontend/src/components/PlayerComparePanel.tsx
- **Committed in:** a298e0b (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 Rule 3 blocking install, 1 Rule 1 type bug, 1 Rule 2 missing critical)
**Impact on plan:** All necessary for TypeScript correctness and correct module resolution. No scope changes.

## Issues Encountered

**Pre-existing build errors (out of scope):**
- `vite.config.ts` — `Cannot find module 'path'` and `Cannot find name '__dirname'` — pre-existing from Phase 0 scaffold (confirmed in Plan 09 SUMMARY). `npm run build` exits 2 due to these. `npx tsc --noEmit` passes cleanly (no composite project errors).

## Known Stubs

- `PlayerDetailDrawer` calls GET `/team/stats/{player_id}?league_id={id}` — this backend route is added in Plan 12. Until then, useQuery returns undefined and TrendChart shows "Stats available in-season" empty state.
- `PlayerComparePanel` calls GET `/team/trade?player_a&player_b&league_id` — this route exists from Plan 05/06. Should work immediately.
- `comparePool` in TeamPage uses lineup data from Plan 06's GET /team/lineup — already exists. Players without `matchup_grade`, `opponent_rank_vs_position`, or `recent_usage_trend` will not render those chips (conditional rendering guards all three fields).

## Threat Flags

None — PlayerDetailDrawer and PlayerComparePanel only display data the user already has access to through the lineup and trade APIs. No new server-side trust boundaries introduced. T-02-11-01, T-02-11-02, T-02-11-03 all have `accept` disposition per plan threat model.

## Next Phase Readiness

- PlayerDetailDrawer, WeatherChip, TrendChart, PlayerComparePanel all complete
- Plan 12 (player-stats backend route) adds the real data source for TrendChart
- TeamPage card stack is now: LineupCard → WaiverCard → StandingsCard + PlayerDetailDrawer modal
- Phase 3+: matchup_grade, opponent_rank_vs_position, recent_usage_trend fields need to be populated from /team/lineup backend response

## Self-Check: PASSED

Files created:
- frontend/src/components/WeatherChip.tsx: EXISTS
- frontend/src/components/TrendChart.tsx: EXISTS
- frontend/src/components/PlayerDetailDrawer.tsx: EXISTS
- frontend/src/components/PlayerComparePanel.tsx: EXISTS
- frontend/src/pages/TeamPage.tsx: EXISTS (modified)

Commits:
- 45df8fa: EXISTS (WeatherChip + TrendChart)
- a298e0b: EXISTS (PlayerDetailDrawer + PlayerComparePanel + TeamPage)

TypeScript (tsc --noEmit): PASSES (exit 0)
Build (npm run build): Only pre-existing vite.config.ts errors; all new files type-check correctly

---
*Phase: 02-team-manager-core*
*Completed: 2026-06-27*
