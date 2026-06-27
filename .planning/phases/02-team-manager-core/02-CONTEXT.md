---
phase: 2
phase_name: Team Manager Core
status: decisions-recorded
created: 2026-06-25
source: discuss-phase interactive session with Paul
---

# Phase 2 Context — Team Manager Core

## Phase Boundary

Phase 2 delivers lineup recommendations, start/sit analysis, player detail panels, injury/availability status, waiver wire suggestions, performance recaps, league standings, trade analysis, season projections, historical trends, positional scarcity, strength-of-schedule analysis, trade value charts, dynasty rankings, and waiver priority tracking. Read-only — no writes back to Sleeper in this phase. Writing to host platforms is Phase 3+.

## Scope Decision

**Full TM-01–16** — all 16 requirements are in scope for this phase. The user explicitly chose full scope over a TM-01–07 MVP cut.

This phase will be structured across multiple plan files. TM-01–07 form the core and should be planned/executed first; TM-08–16 extend the feature set and can be sequenced after.

## Gray Area Decisions

### DECISION-001: Projection Data Source

**Decision:** Dual source — Sleeper API (weekly/injury data) + FantasyCalc API (dynasty/trade values)

**How to implement:**
- **Sleeper** (already integrated): player pool, ADP, injury status, weekly matchups, roster snapshots
- **FantasyCalc** (`https://api.fantasycalc.com/`): free REST API, no auth required, returns dynasty and redraft trade values/rankings
- Combine into a `ProjectionService` that merges both signals:
  - Start/sit ranking: Sleeper ADP as weekly-relevance proxy + FantasyCalc dynasty value for keeper context
  - Lineup optimizer: rank by ADP-adjusted expected value, downweight injured players
  - Trade analyzer (TM-08, TM-13): use FantasyCalc trade values as the authoritative score
  - Dynasty rankings (TM-14): pull directly from FantasyCalc dynasty endpoint

**What this is NOT:** Neither source provides true weekly point projections (e.g., "Patrick Mahomes projects for 28.4 pts"). The optimizer ranks relative value, not absolute point totals. Projected point totals shown in UI should be framed as estimates/proxies based on ADP tier, not precise forecasts.

**Cache strategy:** FantasyCalc data changes infrequently — cache 24 hours in Redis. Sleeper injury/status data should be fresher — cache 1 hour.

**FantasyCalc endpoints to use (VERIFIED 2026-06-26 — previous URLs returned 404):**
- `GET /values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1` — redraft trade values
- `GET /values/current?isDynasty=true&numQbs=1&numTeams=12&ppr=1` — dynasty trade values
- Rankings: use `overallRank` and `positionRank` fields from the `/values/current` response — no separate rankings endpoint exists (all tested variants return 404)

### DECISION-002: UI Layout

**Decision:** Card-based vertical stack (locked in prior session)

TeamPage shows cards stacked vertically:
1. Lineup optimizer card (recommended starting lineup + current lineup side-by-side)
2. Waiver wire card
3. Player detail panel (slide-in drawer or expanded card)
4. Standings/recap card

### DECISION-003: Waiver Wire Formula

**Decision:** Give users selectable formula options — do not force a single algorithm

Two modes exposed in the UI (dropdown or toggle):
- **Trend-weighted**: recent performance weighted more heavily (last 2 weeks > season avg)
- **Full composite**: combines ADP, FantasyCalc value, recent performance, team positional need, and injury risk equally

Backend computes both scores and returns both; frontend lets user toggle which ranking is displayed. The active mode is stored in user preferences (can be localStorage for MVP, migrate to DB in Phase 8).

### DECISION-004: League Switcher

**Decision:** League switcher UI — a persistent UI element for users connected to multiple leagues

Users who have imported multiple leagues need a fast way to switch context. The switcher:
- Lives in the top nav / sidebar (near the league name display)
- Shows all connected leagues with platform icon (Sleeper badge) and season year
- Switching league updates the active league context app-wide (Zustand store)
- Active league ID stored in Zustand; persisted to localStorage so it survives page refresh
- All Team Manager data (lineup, waiver, standings) re-fetches on league switch

## Data Model Notes

No new SQLAlchemy models needed for Phase 2 MVP data. The existing `Roster`, `Team`, `League`, and `LeagueMember` tables from Phase 1 are sufficient for read operations.

New backend structures needed (not DB-persisted, computed on request):
- `ProjectionService` — merges Sleeper + FantasyCalc
- `LineupOptimizer` — ranks players by position given roster snapshot
- `WaiverRanker` — computes trend-weighted and composite scores
- `TradeEvaluator` — wraps FantasyCalc values with league-specific context

## Frontend Notes

- `TeamPage.tsx` already exists as a stub — it calls `GET /api/v1/team/my` which does not exist yet
- New API routes needed: `/api/v1/team/my`, `/api/v1/team/lineup`, `/api/v1/team/waiver`, `/api/v1/team/standings`, `/api/v1/team/trade`
- PlayerCard component already scaffolded in TeamPage.tsx — extend it rather than replace
- League switcher goes in the existing nav shell (check `frontend/src/components/` for layout components)

## Deferred to Phase 3+

- Writing lineup changes back to Sleeper (read-only in Phase 2)
- Yahoo and ESPN data sources for projections
- AI natural-language trade summaries (Phase 7)
- Push notifications for waiver wire pickups or lineup alerts (Phase 8)
- User preference persistence to DB (Phase 8)
- **TM-14 (player news feed):** Deferred — Sleeper has no news endpoint and no free structured source was identified. Phase 2 delivers `news: []` (empty array); the news section in PlayerDetailDrawer is hidden (not shown as empty state) per UI-SPEC. Will be addressed in Phase 2b or Phase 3.

---

*Phase: 02-team-manager-core*
*Context recorded: 2026-06-25 — post-discuss-phase decisions*
*Updated: 2026-06-26 — FantasyCalc URL corrected (verified live); TM-14 formally deferred*
