# Synthesis Summary
# Entry point for gsd-roadmapper
# Produced by gsd-doc-synthesizer

---

## Doc Counts by Type

Total docs consumed: 5
- ADR: 1 (DESIGN_CONCEPTS.md)
- PRD: 2 (PHASES.md, USER_STORIES.md)
- SPEC: 1 (ARCHITECTURE.md)
- DOC: 1 (README.md)

All docs had confidence: high. No UNKNOWN-confidence docs.

---

## Cycle Detection

Cross-ref graph: acyclic. No cycles found. Max traversal depth well under limit (actual depth: 3).
Synthesis proceeded on all 5 docs.

---

## Decisions (ADR)

Locked decisions: 5
Source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md

- DECISION-001: League Connector screen — Option C (Conversational onboarding chat) [LOCKED]
- DECISION-002: Team Manager screen — Option B (Card-based vertical stack) [LOCKED]
- DECISION-003: Draft Room screen — Option B (Bloomberg Terminal high-density) [LOCKED]
- DECISION-004: Trade Evaluator screen — Option C (Decision-tree impact analysis) [LOCKED]
- DECISION-005: Navigation pattern — Option C (Bottom tab bar mobile + top bar desktop) [LOCKED]

Proposed decisions (not voted/locked): 2
- DECISION-006: Design tokens (dark palette, Inter/JetBrains Mono)
- DECISION-007: Cross-screen UX patterns (empty states, loading states, toasts, iconography, accessibility)

Full detail: /c/Users/paul_/git/fantasy-football-hub/.planning/intel/decisions.md

---

## Requirements (PRD)

Requirements extracted: 67

By epic:
- Authentication / Onboarding (X-series): 5 requirements
- League Connector (LC-series): 14 requirements
- Team Manager (TM-series): 16 requirements
- Live Draft Room (DR-series): 20 requirements
- Trade Evaluator (TE-series): 15 requirements
- Data Integrity / Mobile / Notifications (X-series continued): 7 requirements (some counted above)

By tier:
- MVP: 22 requirements
- V1: 33 requirements
- V2: 12 requirements

Phase breakdown (from PHASES.md):
- Phase 0 — Project Setup (~2 weeks / 1 week two-dev)
- Phase 1 — League Connector MVP (~3 weeks one-dev)
- Phase 2 — Team Manager Core (~4–5 weeks one-dev)
- Phase 3 — Multi-Platform Connectors (~4 weeks one-dev)
- Phase 4 — Live Draft Room Snake (~5–6 weeks one-dev)
- Phase 5 — Auction Draft Variant (~2 weeks)
- Phase 6 — Video and Audio (~1.5 weeks)
- Phase 7 — Trade Finder and Evaluator (~5–6 weeks)
- Phase 8 — Polish, Mobile, Performance (~5 weeks)
- Phase 9 — V2 Differentiation (post-V1)

Critical path: Phase 0 → Phase 1 → Phase 2 → (Phase 4 OR Phase 7)
MVP minimum path: Phase 0 → Phase 1 → Phase 2 tasks 2.1–2.4 and 2.8
MVP timeline estimate: 6–8 weeks from project start

Full detail: /c/Users/paul_/git/fantasy-football-hub/.planning/intel/requirements.md

---

## Constraints (SPEC)

Constraints extracted: 15
Source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md

By type:
- tech-stack (5): Backend (FastAPI/Python), Frontend (React/Vite/TS), Styling (Tailwind/shadcn), Real-time (python-socketio + Redis), Background jobs (arq)
- api-contract (2): Video/audio (Daily.co), Authentication (self-hosted JWT + per-platform OAuth)
- schema (1): Primary database (PostgreSQL 16) with full data model sketch
- nfr (6): Cache layer (Redis 7 with TTL table), Rate limits (per-platform budgets), Hosting (Digital Ocean MVP), Mobile strategy (breakpoints, PWA), Performance budget (sub-500ms picks), Security baseline, Observability

Open architecture questions (unresolved, become blockers at specific phases):
1. LLM provider for trade AI (blocker before Phase 7)
2. Hosted vs droplet Postgres for MVP (blocker before Phase 0 deploy)
3. Sleeper as demo/marketing path (decision before Phase 1)
4. CLI for power users (low priority, can stay open)
5. Public read-only league pages (V2, can stay open)

Full detail: /c/Users/paul_/git/fantasy-football-hub/.planning/intel/constraints.md

---

## Context Topics (DOC)

Topics extracted: 5
Source: /c/Users/paul_/git/fantasy-football-hub/README.md

- Project identity and purpose
- Repository layout and file conventions
- Contribution and voting protocol
- Guiding principles (6 non-negotiables)
- Glossary (8 domain terms)

Full detail: /c/Users/paul_/git/fantasy-football-hub/.planning/intel/context.md

---

## Conflict Summary

Blockers: 0
Competing variants: 0
Auto-resolved: 3 (2 ADR > PRD layout overrides; 1 open architecture question flagged for action)

Full detail: /c/Users/paul_/git/fantasy-football-hub/.planning/INGEST-CONFLICTS.md

---

## Status

STATUS: READY — safe to route to gsd-roadmapper

No blockers. No competing variants requiring user resolution. All auto-resolved conflicts are logged with rationale and required follow-up actions noted in the conflicts report.

---

## Downstream Consumer Notes

For gsd-roadmapper:
- DECISION-003 (Draft Room = Bloomberg Terminal) overrides PHASES.md task 4.4 wording. Use DECISION-003.
- DECISION-004 (Trade Evaluator = Decision-tree) overrides PHASES.md task 7.3 wording. Use DECISION-004.
- LLM provider for TE-020 (REQ-te-ai-summary) is provisionally Claude API but must be formally voted before Phase 7.
- Hosted vs droplet Postgres must be decided before Phase 0 deploy target (open architecture question 2).
- Two-team trade is MVP-adjacent V1 scope; multi-team trade is explicit V2.
- Draft Room dependencies: Phase 5 (Auction) requires Phase 4 (Draft); Phase 6 (Video) requires Phase 4 (Draft).
- Parallelizable if two developers: Phase 2 + Phase 3, Phase 4 + Phase 7, Phase 5 + Phase 8.
