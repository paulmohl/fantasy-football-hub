# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-22)

**Core value:** Two users can connect a Sleeper league, view rosters, and get lineup recommendations without leaving the Hub.
**Current focus:** Phase 1 — League Connector MVP

## Current Position

Phase: 2 of 8 active phases (Team Manager Core)
Plan: 1 of 12 in current phase (02-01-PLAN.md complete)
Status: In progress
Last activity: 2026-06-27 — 02-01 Wave 0 test scaffolding complete (stubs + fixtures + npm packages)

Progress: [██░░░░░░░░] ~15% (Phase 0 complete; Phase 1 complete; Phase 2 plan 1/12 complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: ~15 minutes
- Total execution time: ~0.25 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 0. Setup | complete | — | — |
| 2. Team Manager Core | 02-01 | ~15 min | ~15 min |

**Recent Trend:** No data yet.

*Updated after each plan completion*

## Accumulated Context

### Decisions

All locked decisions are in PROJECT.md Key Decisions table. Summary for current work:

- DECISION-001 (League Connector): Conversational onboarding chat — LOCKED
- DECISION-002 (Team Manager): Card-based vertical stack — LOCKED
- DECISION-003 (Draft Room): Bloomberg Terminal high-density layout — LOCKED
- DECISION-004 (Trade Evaluator): Decision-tree impact analysis — LOCKED
- DECISION-005 (Navigation): Bottom tab bar mobile + top rail desktop — LOCKED
- PostgreSQL chosen over SQLite (explicit override for multi-process draft room)
- Sleeper-first because no OAuth required (fastest MVP path)

### Pending Todos

- Wave 0 test scaffolding (02-01) complete; next is Wave 1: 02-02 (ProjectionService) and 02-03 (WeatherService)

### Blockers / Concerns

- **Before Phase 0 deploy (open)**: Hosted vs droplet Postgres decision needed — open architecture question from ARCHITECTURE.md
- **Before Phase 7**: LLM provider for trade AI must be voted (provisionally Claude API)
- **Before Phase 1**: Sleeper as "demo without auth" marketing path — decide whether to enable anonymous read-only view
- **Hard deadline**: Draft Room (Phase 4) must be ready before end of August 2026; Phase 1 → 2 → 3 → 4 must complete in sequence before that date

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| V2 | Mock draft AI opponents | Backlog | Planning |
| V2 | Multi-team (3+) trades | Backlog | Planning |
| V2 | Counter-offer AI suggestion | Backlog | Planning |
| V2 | Trade history + retrospective grades | Backlog | Planning |
| V2 | NFL.com platform connector | Backlog | Planning |
| V2 | Dynasty rookie draft support | Backlog | Planning |
| V2 | iOS/Android native wrapper | Backlog | Planning |

## Session Continuity

Last session: 2026-06-27
Stopped at: 02-01 complete (Wave 0 test scaffolding). Next: 02-02 (cache.py extensions + ProjectionService)
Resume file: None
