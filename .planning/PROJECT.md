# Fantasy Football Hub

## What This Is

Fantasy Football Hub is a serious multi-platform fantasy football companion for competitive leagues — the kind with side bets, keeper rules, draft-night rituals, and a commissioner with opinions. It connects to Sleeper, Yahoo, and ESPN leagues and provides lineup optimization, a live draft room with chat and video, and a trade evaluator with AI-powered analysis. Built by and for the league that already exists in a group chat.

## Core Value

Two users can connect a Sleeper league, view their rosters, and get lineup recommendations — without needing to leave the Hub to make decisions.

## Runtime / Deployment

- **Local dev**: Docker Compose (Postgres + Redis + FastAPI app + arq worker + Vite dev server)
- **Production**: Single Digital Ocean droplet, systemd + nginx, PM2 not used (Python app via systemd unit)
- **Hard deadline**: Draft Room (Phase 4) ready before end of August 2026

## Requirements

### Validated

- ✓ Project scaffold complete — Phase 0 (FastAPI, Socket.IO, Alembic, Redis, Vite/React/Tailwind)

### Active

- [ ] Users can sign up and sign in (email/password + Google OAuth)
- [ ] Users can connect a Sleeper league and view its settings, rosters, and members
- [ ] Team Manager: lineup view, optimal lineup, start/sit recommendations, waiver wire ranked by need
- [ ] Users can connect Yahoo and ESPN leagues with feature parity to Sleeper
- [ ] Live Draft Room for snake drafts with real-time board, chat, and Bloomberg Terminal aesthetic
- [ ] Auction draft variant inside the same draft room infrastructure
- [ ] Optional video/audio (Daily.co) for draft night
- [ ] Trade Finder and Evaluator with decision-tree impact analysis and AI summary
- [ ] Polish, mobile responsiveness, notifications, and PWA

### Out of Scope

| Feature | Reason |
|---------|--------|
| Cash dues / commissioner payments | Not fantasy tooling, legal complexity |
| League creation | Platform hosts the league of record |
| Survivor pools, pick'em, DFS | Different product domain |
| Player social feed beyond curated news | Scope creep, not core value |
| Public league discovery / matchmaking | V2 consideration |
| Native mobile apps (iOS/Android) | PWA only through V1 |
| White-label / multi-tenant beyond per-user isolation | Not the target market |
| Multi-team (3+) trades | V2 — two-team is the MVP-adjacent V1 scope |
| Custom scoring rule editor | V2 — flag unmodeled rules instead |
| NFL.com platform connector | V2 |
| Mock draft AI opponents | V2 stretch at earliest |

## Context

- Phase 0 is complete: FastAPI scaffold, Socket.IO, Alembic migrations, Redis integration, and the frontend scaffold (Vite + React 18 + TypeScript + Tailwind) all exist in the repo.
- Phase 1 (League Connector MVP) is the current active phase.
- MVP = Phases 0+1+2 minimum. Minimum Phase 2 scope = tasks 2.1–2.4 and 2.8.
- Sleeper is the first connector because it requires no OAuth — a user can connect a public league in under 30 seconds.
- The draft room is a feature, not a separate app — it shares data model, auth, and design language.
- PostgreSQL is an explicit override of Paul's SQLite default: multi-process draft room and real-time fan-out require Postgres.
- Open architecture question: Hosted vs droplet Postgres (must resolve before Phase 0 deploy).
- Open architecture question: LLM provider for trade AI — provisionally Claude API, must be voted before Phase 7.

## Constraints

- **Tech stack (backend)**: Python 3.12 + FastAPI — async-native, consistent with existing fantasybbleague work
- **Tech stack (frontend)**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui (copy-in, not a dependency)
- **Real-time**: python-socketio + Redis adapter — namespaces /league and /draft; draft lock via Redis key
- **Database**: PostgreSQL 16 — JSONB for scoring_rules, roster_format, rosters.snapshot; deduped by (host_platform, host_league_id, season)
- **Cache**: Redis 7 — per-key TTL table in ARCHITECTURE.md; invalidation: event-driven > write-through > TTL fallback
- **Background jobs**: arq (asyncio-native, Redis-backed)
- **Auth**: Self-hosted JWT (python-jose + Argon2); 15-min access tokens + 30-day rotating refresh tokens in httpOnly cookies; per-user envelope key encryption for OAuth credentials
- **Video/Audio**: Daily.co managed WebRTC — pay-per-minute, ~$11 per 12-team 4-hour draft
- **Hosting**: Single Digital Ocean droplet for MVP, ~$50/month budget ceiling
- **Mobile**: Single React codebase, breakpoint-driven (phone < 640px, tablet 640–1024px, desktop > 1024px); PWA install after first league connection
- **Performance**: Sub-500ms pick propagation p99; most reads from cache
- **Security**: Credentials encrypted at rest, TLS everywhere, Pydantic validation on every endpoint, audit log for sensitive actions
- **Timeline**: Draft Room (Phase 4) must be ready before end of August 2026

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DECISION-001: League Connector screen — Option C (Conversational onboarding chat) | Differentiated; approachable; easy to extend with help replies. LOCKED — do not re-open. | — Pending |
| DECISION-002: Team Manager screen — Option B (Card-based vertical stack) | Scannable; excellent on mobile; friendly to new users. LOCKED — do not re-open. | — Pending |
| DECISION-003: Draft Room screen — Option B (Bloomberg Terminal high-density) | Maximum info per pixel; power-user gold; unlike any other fantasy app. LOCKED — do not re-open. | — Pending |
| DECISION-004: Trade Evaluator screen — Option C (Decision-tree impact analysis) | Most decision-useful; treats user as smart; differentiated. LOCKED — do not re-open. | — Pending |
| DECISION-005: Navigation — Option C (Bottom tab bar mobile + top rail desktop) | Best mobile pattern; Draft Room overrides to full-screen broadcast mode. LOCKED — do not re-open. | — Pending |
| DECISION-006: Design tokens — dark-first palette, Inter + JetBrains Mono (proposed, not locked) | Draft Room always dark regardless of user preference. | — Pending |
| DECISION-007: Cross-screen UX patterns — skeletons, toasts, Lucide React icons, WCAG 2.1 AA (proposed) | Accessibility and loading states standardized across all screens. | — Pending |
| PostgreSQL over SQLite | Multi-process draft room + real-time fan-out require row-level locking and concurrent connections | — Pending |
| Sleeper-first connector | No OAuth required — fastest path to MVP without platform registration | — Pending |
| Draft Room before Trade Evaluator | Hard deadline: August 2026 draft season; Draft Room is the marquee feature | — Pending |

---
*Last updated: 2026-06-22 after initial project initialization*
