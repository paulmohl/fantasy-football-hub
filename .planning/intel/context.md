# Context Intel
# Source: README.md (DOC, locked: false)
# Synthesized by gsd-doc-synthesizer

---

## Topic: Project Identity and Purpose

source: /c/Users/paul_/git/fantasy-football-hub/README.md

Fantasy Football Hub is a serious fantasy football platform built for competitive leagues — the kind with side bets, keeper rules, draft-night rituals, and a commissioner with opinions. Not built for the casual majority. Built for the league that already exists in a group chat.

The four pillars: League Connector, Team Manager, Live Draft Room, Trade Finder & Evaluator.

Status at time of planning: Planning and design voting phase. No production code written. All five planning documents are the source of truth for what to build, why, how, and in what order.

Owners: Paul Mohl (architecture, backend lead); TBD collaborator (frontend lead, product input).

Target start of build: Once Phase 0 sign-off is recorded in a tracking issue.

Live mockups (GitHub Pages): https://paulmohl.github.io/fantasy-football-hub/mockups/

---

## Topic: Repository Layout

source: /c/Users/paul_/git/fantasy-football-hub/README.md

Planning repo with five root files:
- README.md — project overview, voting protocol, status
- USER_STORIES.md — full Gherkin user stories organized by epic
- ARCHITECTURE.md — tech stack rationale, data flow, caching, real-time design
- DESIGN_CONCEPTS.md — three UI directions per major screen, ASCII wireframes
- PHASES.md — MVP / V1 / V2 work breakdown with S/M/L/XL effort tags

Rule: Always edit those five files directly when proposing a change. Do not create parallel drafts.

---

## Topic: Contribution and Voting Protocol

source: /c/Users/paul_/git/fantasy-football-hub/README.md

Two-person planning forum. Discussion in GitHub Issues.

Issue labels:
- design-vote — presents 2+ options, asks for a decision, vote with reactions
- feature-request — add a story or capability to an epic
- architecture — challenge or extend the tech stack rationale
- blocker — a decision must be made before downstream work can start
- nice-to-have — idea worth recording but not required for any phase

Voting protocol for design-vote issues:
1. Issue body lists each option as a numbered section with a clear name.
2. Each voter reacts on the option header comment with thumbs-up.
3. Thumbs-down is a soft veto and must be paired with a written objection.
4. After 72 hours (or both voters have weighed in), winner is recorded by editing the relevant planning doc and closing the issue with a link to the commit.

Adding a user story:
1. Open a feature-request issue using Gherkin pattern.
2. Tag the epic (league-connector, team-manager, draft-room, trade-evaluator).
3. Once both voters agree, story appended to USER_STORIES.md via PR requiring one approval.

Disagreement protocol: record both positions in the relevant doc under Open Questions, label it blocker, time-box a resolution. Default winner if no resolution by time-box: the option requiring less work for MVP.

---

## Topic: Guiding Principles

source: /c/Users/paul_/git/fantasy-football-hub/README.md

1. Working solution first. Ship the dumb version, then improve.
2. Read-only mode must work without OAuth. A new user should paste a public Sleeper league ID and see something useful in under 30 seconds.
3. Cache aggressively, invalidate on write. Treat host platforms as expensive APIs. Cache is the system of record between fetches.
4. The draft room is a feature, not a separate app. It shares data model, auth, and design language with the rest of the app.
5. Mobile-responsive, not mobile-first. Sunday morning usage is mobile; draft night is desktop. Both must feel intentional.
6. Dark mode default. Light mode optional. Inspired by Sleeper and ESPN broadcast aesthetic.

---

## Topic: Glossary

source: /c/Users/paul_/git/fantasy-football-hub/README.md

Host platform — Yahoo, Sleeper, ESPN, NFL.com — the system that owns the league of record.
Connection — a linked league belonging to a user; one user can have many.
League — the deduplicated logical league across all members who have connected to it.
Roster slot — a position in a team's lineup (QB, RB1, FLEX, BN, IR, etc.).
Pick — a single selection in a draft, identified by (league_id, round, slot).
Confidence score — a 0–100 internal score for start/sit and trade recommendations.
Two-sided trade — trade involving exactly two teams (MVP scope).
Multi-team trade — 3+ team trade (deferred to V2).

---

## Topic: Quick Stack Summary (from DOC perspective)

source: /c/Users/paul_/git/fantasy-football-hub/README.md

Note: Full rationale is in ARCHITECTURE.md (synthesized in constraints.md). This is the README-level summary for contributor orientation.

Backend: Python 3.12 + FastAPI — async-native, familiar from fantasybbleague, ecosystem fit for analytics.
Frontend: React 18 + Vite + TypeScript + Tailwind — component model, fast iteration.
Real-time: WebSockets via python-socketio + Redis adapter — single mechanism for draft, chat, trade pings, live scoring.
Video/Audio: Daily.co (managed WebRTC) — avoids running own TURN/SFU; pay-per-minute.
Cache: Redis 7 — per-league TTL, pub/sub for fan-out, rate-limit counters.
Primary DB: PostgreSQL 16 — relational, JSONB for scoring rules, mature tooling.
Auth: OAuth 2.0 per platform + app-level JWT sessions.
Hosting: Single Digital Ocean droplet for MVP; Fly.io or Render for V1.
