# Fantasy Football Hub

A serious fantasy football platform for serious leagues — real-time draft rooms with broadcast aesthetics, intelligent lineup management, deep trade analytics, and first-class integrations with the major host platforms.

This repository is the **planning workspace**. No production code has been written yet. The five documents in this repo are the source of truth for what we are building, why, how, and in what order.

---

## Status

**Phase:** Planning and design voting
**Owners:** Paul Mohl (architecture, backend lead), TBD collaborator (frontend lead, product input)
**Target start of build:** Once Phase 0 sign-off is recorded in a tracking issue

---

## What We Are Building

Most fantasy football apps are built for the casual majority. They are competent but generic. Fantasy Football Hub is built for the league that already exists in a group chat — the one with side bets, keeper rules nobody remembers, draft-night rituals, and a commissioner who has opinions. Every feature on this roadmap is designed around how competitive leagues actually behave.

### The Four Pillars

| # | Feature | One-line summary | Doc anchor |
|---|---------|------------------|------------|
| 1 | **League Connector** | Connect a league from Yahoo, Sleeper, ESPN, or NFL.com; detect format, settings, scoring, and roster shape | [User Stories](USER_STORIES.md#epic-1--league-connector) |
| 2 | **Team Manager** | Weekly lineup decisions with confidence-scored start/sit, weather, injury, and matchup context; waiver targets ranked by need | [User Stories](USER_STORIES.md#epic-2--team-manager) |
| 3 | **Live Draft Room** | An immersive draft experience modeled on the NFL Draft broadcast — dark room, podium, real-time pick board, chat, optional video | [User Stories](USER_STORIES.md#epic-3--live-draft-room) |
| 4 | **Trade Finder & Evaluator** | Propose, analyze, and negotiate trades with an AI-assisted evaluator that explains *why*, not just *who wins* | [User Stories](USER_STORIES.md#epic-4--trade-finder--evaluator) |

---

## Repository Layout

This is a planning repo. Five files at the root, each one a deliverable:

```
.
├── README.md            # This file — project overview, how to vote, status
├── USER_STORIES.md      # Full Gherkin user stories, organized by epic
├── ARCHITECTURE.md      # Tech stack rationale, data flow, caching, real-time design
├── DESIGN_CONCEPTS.md   # Three UI directions per major screen, ASCII wireframes
└── PHASES.md            # MVP / V1 / V2 work breakdown with S/M/L/XL effort tags
```

Optional supporting folders may appear later (`/designs` for image mockups, `/.github` for issue templates), but the planning content lives in those five Markdown files. **Always edit those files directly when proposing a change** — do not create parallel drafts.

---

## How to Contribute and Vote

This repo is run as a small two-person planning forum. Discussion happens in GitHub Issues. The following labels are the contract:

| Label | Use it when |
|-------|-------------|
| `design-vote` | An issue presents 2 or more options and asks for a decision. Vote with reactions. |
| `feature-request` | You want to add a story, capability, or edge case to one of the four epics. |
| `architecture` | You want to challenge or extend the tech stack rationale in `ARCHITECTURE.md`. |
| `blocker` | A decision must be made before downstream work can start. |
| `nice-to-have` | An idea worth recording but not required for any phase. |

### Voting protocol

For any issue tagged `design-vote`:

1. The issue body must list each option as a numbered section with a clear name (e.g. **Option A — Sidebar Navigation**).
2. Each voter reacts on the option header comment, **not the issue itself**, with a thumbs-up.
3. A thumbs-down on a header comment is a soft veto and must be paired with a written objection.
4. After 72 hours (or both voters have weighed in), the winner is recorded by editing the relevant planning doc and closing the issue with a link to the commit.

### Adding a user story

1. Open a `feature-request` issue. Use the Gherkin pattern (Given / When / Then).
2. Tag the epic (`league-connector`, `team-manager`, `draft-room`, `trade-evaluator`).
3. Once both voters agree, the story is appended to `USER_STORIES.md` in a PR. PRs against planning docs require one approval.

### Disagreement protocol

If the two of us disagree on a meaningful decision, we record both positions in the relevant doc under a `## Open Questions` section, label it `blocker`, and time-box a resolution. Default winner if no resolution by the time-box: the option that requires less work for MVP.

---

## Quick Stack Summary

This is the proposed stack. Full rationale and alternative comparisons are in [ARCHITECTURE.md](ARCHITECTURE.md).

| Layer | Choice | Rationale (short) |
|-------|--------|-------------------|
| Backend | Python 3.12 + FastAPI | Async-native, familiar from `fantasybbleague`, ecosystem fit for analytics |
| Frontend | React 18 + Vite + TypeScript + Tailwind | Component model, fast iteration, broad hireability if we ever expand |
| Real-time | WebSockets via `python-socketio` + Redis adapter | Single mechanism for draft, chat, trade pings, live scoring |
| Video / Audio | Daily.co (managed WebRTC) | Avoids running our own TURN/SFU; pay-per-minute scales with usage |
| Cache | Redis 7 | Per-league TTL, pub/sub for fan-out, rate-limit counters |
| Primary DB | PostgreSQL 16 | Relational, JSONB for scoring rules, mature tooling |
| Auth | OAuth 2.0 per platform + app-level JWT sessions | Each platform integration uses its own OAuth flow |
| Hosting | Single Digital Ocean droplet for MVP; Fly.io or Render for V1 | Matches existing infra; defer Kubernetes forever |

---

## Guiding Principles

A few non-negotiables that should constrain every decision:

1. **Working solution first.** Ship the dumb version, then improve. Mirrors the rule that built `fantasybbleague`.
2. **Read-only mode must work without OAuth.** A new user should be able to paste a public Sleeper league ID and see something useful in under 30 seconds.
3. **Cache aggressively, invalidate on write.** Treat host platforms as expensive APIs (because they are). The cache is the system of record between fetches.
4. **The draft room is a feature, not a separate app.** It shares the data model, auth, and design language with the rest of the app.
5. **Mobile-responsive, not mobile-first.** Most usage on Sunday morning will be mobile. Most usage during draft night will be desktop. Both must feel intentional.
6. **Dark mode default. Light mode optional.** Inspired by Sleeper and ESPN broadcast aesthetic.

---

## Glossary

A small glossary so issue threads stay consistent.

| Term | Meaning here |
|------|--------------|
| **Host platform** | Yahoo, Sleeper, ESPN, NFL.com — the system that owns the league of record |
| **Connection** | A linked league belonging to a user; one user can have many |
| **League** | The deduplicated logical league across all members who have connected to it |
| **Roster slot** | A position in a team's lineup (QB, RB1, FLEX, BN, IR, etc.) |
| **Pick** | A single selection in a draft, identified by `(league_id, round, slot)` |
| **Confidence score** | A 0–100 internal score for start/sit and trade recommendations |
| **Two-sided trade** | Trade involving exactly two teams (MVP scope) |
| **Multi-team trade** | 3+ team trade (deferred to V2) |

---

## Where to Go Next

- New here? Read `USER_STORIES.md` first. It is the easiest entry point.
- Joining as a builder? Read `ARCHITECTURE.md` and `PHASES.md` together.
- Voting on UI directions? Open `DESIGN_CONCEPTS.md`, find the screen, react on the option you prefer in the matching issue.
- Looking for what is in scope and what is not? `PHASES.md` is the definitive source.
