# Phases and Work Breakdown

This document defines what we build, in what order, and roughly how much work each chunk represents. The goal is to ship a working MVP fast, then iterate.

## Effort Tags

| Tag | Range | What it means |
|-----|-------|---------------|
| **S** | < 1 day | A focused afternoon. One developer, one sitting. |
| **M** | 1–3 days | A self-contained piece of work. |
| **L** | 3–7 days | Spans multiple subsystems or requires meaningful design. |
| **XL** | 1.5–3 weeks | A major feature on its own. Requires breakdown into sub-issues before starting. |

All estimates assume one developer working with reasonable focus. Multiply by ~1.5x if both developers are coordinating on the same code.

## Release Tiers

| Tier | Definition | Target audience |
|------|------------|-----------------|
| **MVP** | The smallest thing worth using. One person can run their league on it. Probably one developer's home league as the test bed. | The two of us + immediate friends |
| **V1** | The thing we would feel comfortable sharing on a fantasy football subreddit. Polish, mobile, real-time. | Early adopters who want a Sleeper alternative |
| **V2** | Differentiating depth. Dynasty tooling, advanced trade analytics, multi-team trades, mobile PWA. | Power users and content creators |

---

# Phase 0 — Project Setup

**Goal:** Repo, environments, deploy pipeline. Everything we need to start writing feature code.

| ID | Task | Effort | Notes |
|----|------|--------|-------|
| 0.1 | Initialize backend (`fastapi`, `python-socketio`, `arq`, `redis`, `psycopg`, `pydantic-settings`) | S | |
| 0.2 | Initialize frontend (Vite, React 18, TS, Tailwind, shadcn/ui, React Query, React Router) | S | |
| 0.3 | Local dev via `docker-compose.yml` (Postgres, Redis, app, worker) | M | Must run end-to-end with one command |
| 0.4 | CI: lint, type-check, test, build on every PR (GitHub Actions) | S | |
| 0.5 | Deploy to a Digital Ocean droplet (single box, systemd, nginx, Caddy or Let's Encrypt) | M | Pattern matches `MonetizedHRD` |
| 0.6 | Sentry, structured logging, basic health endpoint | S | |
| 0.7 | Secrets management: `.env` for local, environment vars on droplet, documented in README | S | |
| 0.8 | Issue templates and PR template | S | |

**Phase 0 total: ~2 weeks for one dev / 1 week for two.**

---

# Phase 1 — League Connector MVP

**Goal:** A user can sign in, connect a Sleeper league, and view its settings and rosters. No write actions yet. Sleeper-only at first because no OAuth is required.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 1.1 | X-001, X-002 | App auth: email/password + Google OAuth | M | MVP |
| 1.2 | X-001 | Email verification, password reset | M | MVP |
| 1.3 | LC-001 | Sleeper username -> list of leagues | S | MVP |
| 1.4 | LC-001 | Import a selected Sleeper league (settings, roster format, members) | M | MVP |
| 1.5 | LC-010, LC-011, LC-012 | Detect draft type, scoring rules, roster slots from Sleeper data | M | MVP |
| 1.6 | LC-020 | "My connections" page with health status | S | MVP |
| 1.7 | LC-021 | Manual refresh button per league | S | MVP |
| 1.8 | LC-030 | Multi-tenant safety: route guards, query filters, integration tests | M | MVP |
| 1.9 | — | Data model migrations: users, oauth_credentials, leagues, league_members, teams, rosters | M | MVP |
| 1.10 | — | Redis cache layer with TTLs from `ARCHITECTURE.md` Section 5 | M | MVP |
| 1.11 | LC-031 | League dedup across users (same `host_platform + host_league_id + season`) | M | MVP |

**Phase 1 total: ~3 weeks for one dev.**

**Exit criteria:**
- Two test users can each sign up, connect a Sleeper league (same or different), and see settings
- Refresh re-pulls data without errors
- Cache hit rate above 80% on the league settings endpoint after the first fetch

---

# Phase 2 — Team Manager Core

**Goal:** Once a league is connected, the user can view their lineup with start/sit suggestions, browse the waiver wire, and inspect player history. Read-only — no writes to host platform yet.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 2.1 | — | Player ID mapping table; ingest Sleeper player metadata daily | M | MVP |
| 2.2 | TM-001 | Optimal lineup solver (deterministic, constraint-satisfaction over eligibility) | L | MVP |
| 2.3 | TM-001, TM-002 | Lineup view: current vs optimal, projected totals | M | MVP |
| 2.4 | TM-010 | Per-player detail panel: projection, matchup, injury, weather, recent usage | L | MVP |
| 2.5 | TM-011 | Compare two players head-to-head | M | V1 |
| 2.6 | TM-020 | Ingest injury feeds (NFL feed + Sleeper player updates) | M | MVP |
| 2.7 | TM-021 | Weather data via OpenWeather or similar; tag outdoor games | M | V1 |
| 2.8 | TM-030 | Waiver wire ranked by need (composite score) | L | MVP |
| 2.9 | TM-031 | Suggested drops when adding a target | S | MVP |
| 2.10 | TM-032 | FAAB bid recommendations | M | V1 |
| 2.11 | TM-040 | Player season trend chart | M | V1 |
| 2.12 | TM-041 | Player news feed (curated) | M | V1 |
| 2.13 | TM-003 | Write lineup change to host platform (Sleeper writes, then Yahoo/ESPN later) | L | V1 |

**Phase 2 total: ~4–5 weeks for one dev, longer if both contributing to same area.**

**Exit criteria:**
- A user can open Team Manager, see lineup recommendations with confidence scores, and read a clear explanation for the top call
- Waiver wire ranks at least 30 viable targets per league

---

# Phase 3 — Multi-Platform Connectors

**Goal:** Yahoo and ESPN supported with feature parity to Sleeper.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 3.1 | LC-002 | Yahoo OAuth integration: app registration, redirect flow, token storage | L | MVP |
| 3.2 | LC-002 | Yahoo: pull leagues, settings, rosters, scoring | L | MVP |
| 3.3 | LC-003, LC-004 | ESPN: cookie-based auth (private), league-ID public path | M | MVP |
| 3.4 | LC-003 | ESPN: pull leagues, settings, rosters | L | MVP |
| 3.5 | LC-022 | Broken-connection detection + user-facing banner | M | MVP |
| 3.6 | — | Per-platform rate-limit budgets in Redis | M | MVP |
| 3.7 | — | Player ID cross-mapping (Yahoo IDs ↔ ESPN IDs ↔ Sleeper IDs) | L | MVP |
| 3.8 | LC-013 | Keeper / dynasty rule detection | M | V1 |
| 3.9 | — | NFL.com support | L | V2 |

**Phase 3 total: ~4 weeks for one dev.**

**Exit criteria:**
- A user can connect any Yahoo or ESPN league and see the same Team Manager experience as on Sleeper
- Rate limits never exceed our budget

---

# Phase 4 — Live Draft Room (Snake)

**Goal:** A real-time draft room for snake drafts. Broadcast aesthetic. Chat. No video yet.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 4.1 | DR-001, DR-002 | Draft scheduling and order configuration | M | V1 |
| 4.2 | DR-003, DR-004 | Cheat sheets and personal rankings (import + edit) | L | V1 |
| 4.3 | DR-010 | Draft room shell: stage, board, queue, chat panes | L | V1 |
| 4.4 | DR-010 | Broadcast aesthetic CSS pass (Option A or C from `DESIGN_CONCEPTS.md`) | M | V1 |
| 4.5 | DR-050 | Draft board grid component (live updates) | M | V1 |
| 4.6 | DR-011 | "On the clock" stage + countdown | M | V1 |
| 4.7 | DR-012 | Pick submission flow with optimistic update + server confirm | M | V1 |
| 4.8 | DR-013 | Auto-pick on timeout (queue, then ADP fallback) | M | V1 |
| 4.9 | DR-014 | Commissioner pause/resume | S | V1 |
| 4.10 | DR-030 | Draft chat (Socket.IO room, persisted in DB) | M | V1 |
| 4.11 | DR-031 | Pick reactions (emoji badges) | S | V1 |
| 4.12 | DR-052 | Post-draft recap (grades, value picks, log, export) | L | V1 |
| 4.13 | DR-015 | Mock draft mode (solo vs AI) | XL | V2 |
| 4.14 | — | Real-time infra: Socket.IO + Redis adapter + draft lock | L | V1 |
| 4.15 | — | Reconnect with event replay from Redis stream | M | V1 |
| 4.16 | — | Sync draft results back to host platform after completion (Sleeper only initially) | L | V1 |

**Phase 4 total: ~5–6 weeks for one dev. This is the marquee phase.**

**Exit criteria:**
- 12 simultaneous participants can draft from 12 different devices without drift
- Pick propagation p99 under 500ms in a regional test (same country)
- Chat works without dropping messages on reconnect

---

# Phase 5 — Auction Draft Variant

**Goal:** Auction drafts work end-to-end inside the same draft room.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 5.1 | DR-020 | Nomination UI and server event | M | V1 |
| 5.2 | DR-021 | Bidding UI + atomic bid handling on server (CAS pattern in Redis) | L | V1 |
| 5.3 | DR-022 | Auction won + sold animation + roster update | M | V1 |
| 5.4 | DR-023 | Budget constraint enforcement | S | V1 |
| 5.5 | — | Auction-specific recap (budget efficiency, dollars per starter) | M | V1 |

**Phase 5 total: ~2 weeks.**

---

# Phase 6 — Video and Audio for Draft

**Goal:** Optional video and audio inside the draft room. Daily.co integration.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 6.1 | DR-040 | Daily.co room provisioning per draft | M | V1 |
| 6.2 | DR-040 | Video tile strip UI | M | V1 |
| 6.3 | DR-041 | Audio-only join path | S | V1 |
| 6.4 | DR-042 | Push-to-talk option | S | V2 |
| 6.5 | DR-043 | Graceful video failure (rest of room keeps working) | S | V1 |
| 6.6 | — | Video room close + recording cleanup post-draft | S | V1 |

**Phase 6 total: ~1.5 weeks.**

---

# Phase 7 — Trade Finder & Evaluator

**Goal:** Two-team trades. Value comparison. AI summary.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 7.1 | TE-001, TE-002 | Trade builder UI (two-team, drag and drop) | L | V1 |
| 7.2 | TE-003, TE-004 | Submit, cancel, accept, reject flows | M | V1 |
| 7.3 | TE-010 | Side-by-side value totals (Option A from `DESIGN_CONCEPTS.md`) | M | V1 |
| 7.4 | TE-011 | Multiple value lenses (ROS, dynasty, playoff, scarcity) | L | V1 |
| 7.5 | TE-012 | Roster impact: lineup before/after | L | V1 |
| 7.6 | TE-020 | AI natural-language summary (Claude API) | L | V1 |
| 7.7 | TE-021 | Hidden cost flags | M | V1 |
| 7.8 | TE-022 | Counter-offer suggestion | L | V2 |
| 7.9 | TE-030 | Trade notifications (in-app + email + push) | M | V1 |
| 7.10 | TE-031 | Accept / reject / counter from incoming view | M | V1 |
| 7.11 | TE-032 | Expiration handling (background job + email) | S | V1 |
| 7.12 | TE-040 | League trade history with retrospective grades | M | V2 |
| 7.13 | TE-041 | Team trade pattern profile | M | V2 |
| 7.14 | TE-042 | Veto risk indicator | S | V2 |
| 7.15 | — | Multi-team (3+) trade builder | XL | V2 |

**Phase 7 total: ~5–6 weeks.**

**Exit criteria:**
- A user can propose a two-team trade, see value math, see AI summary, send it, and have the recipient accept it
- Trade evaluation under 2 seconds for the deterministic part; AI summary under 5 seconds

---

# Phase 8 — Polish, Mobile, Performance

**Goal:** Make it good. Make it fast. Make it work on a phone.

| ID | Story IDs | Task | Effort | Tier |
|----|-----------|------|--------|------|
| 8.1 | X-020, X-021 | Mobile layouts for every screen | XL | V1 |
| 8.2 | — | PWA manifest, service worker, offline read | M | V1 |
| 8.3 | X-010, X-011 | Notifications system: preferences, email, push, quiet hours | L | V1 |
| 8.4 | — | Performance: query optimization, cache hit-rate dashboard, lazy-loaded routes | L | V1 |
| 8.5 | — | Accessibility audit + fixes (WCAG 2.1 AA baseline) | M | V1 |
| 8.6 | — | Empty states, loading states, error states per screen | M | V1 |
| 8.7 | — | Marketing site / landing page | M | V1 |
| 8.8 | — | Onboarding tour (first-time user) | M | V1 |
| 8.9 | X-030, X-031 | Stale-data UX (banner, read-only fallback when upstream down) | M | V1 |

**Phase 8 total: ~5 weeks. Can run partially in parallel with Phase 7.**

---

# Phase 9 — V2 Differentiation

Reserved for after V1 ships. Sized in `XL` chunks.

| ID | Feature | Effort |
|----|---------|--------|
| 9.1 | Dynasty rookie draft support | XL |
| 9.2 | Multi-team trades | XL |
| 9.3 | Mock draft AI opponents with personality (cautious GM, gunslinger, etc.) | XL |
| 9.4 | League power rankings + weekly recap email | L |
| 9.5 | Public read-only draft recap pages (shareable) | M |
| 9.6 | CLI for power users (terminal-first stats) | L |
| 9.7 | iOS / Android native wrapper (capacitor or expo) | XL |
| 9.8 | NFL.com platform support | L |
| 9.9 | Custom scoring rule editor for unmodeled rules | L |
| 9.10 | Survivor pool side-feature (low priority) | XL |

---

# Dependency Graph

```
                       +---------+
                       | Phase 0 |
                       +----+----+
                            |
                            v
                       +---------+
                       | Phase 1 |  League Connector MVP (Sleeper)
                       +----+----+
                            |
              +-------------+--------------+-------------------+
              |             |              |                   |
              v             v              v                   v
         +---------+   +---------+   +---------+         +---------+
         | Phase 2 |   | Phase 3 |   | Phase 4 |         | Phase 7 |
         +----+----+   +----+----+   +----+----+         +----+----+
         Team Manager  Multi-platform Draft Room         Trade Eval
              |             |              |                   |
              |             |              v                   |
              |             |         +---------+              |
              |             |         | Phase 5 |              |
              |             |         +----+----+              |
              |             |         Auction                  |
              |             |              |                   |
              |             |              v                   |
              |             |         +---------+              |
              |             |         | Phase 6 |              |
              |             |         +----+----+              |
              |             |         Video/Audio              |
              |             |              |                   |
              +-------------+--------------+-------------------+
                            |
                            v
                       +---------+
                       | Phase 8 |   Polish, Mobile, Perf
                       +----+----+
                            |
                            v
                       +---------+
                       | Phase 9 |   V2 Differentiation
                       +---------+
```

### Critical Path

The shortest path to a usable product:

`Phase 0 → Phase 1 → Phase 2 → (Phase 4 OR Phase 7)`

Phases 2, 3, 4, and 7 can run in parallel after Phase 1 lands, **if we have two developers**. With one developer, they should be sequential.

### Parallelizable Pairs

If two developers are working:

- Phase 2 (Team Manager) ↔ Phase 3 (Multi-platform) — different files, minimal merge conflict
- Phase 4 (Draft) ↔ Phase 7 (Trade) — different domains, share only the player data model
- Phase 5 (Auction) ↔ Phase 8 (Mobile/Polish) — independent

### Non-Parallelizable

- Phase 5 (Auction) requires Phase 4 (Draft) — shares the draft room infrastructure
- Phase 6 (Video) requires Phase 4 (Draft) — needs the room shell to exist
- Phase 8 (Polish) can start during Phase 7 but should finish after everything else is in

---

# MVP Definition (Sharp Cut)

For the avoidance of ambiguity, here is the exact MVP scope:

**In:**
- Sign up, sign in (email + Google)
- Connect a Sleeper league
- View league settings, rosters, members
- Team Manager: lineup view, optimal lineup, basic start/sit, waiver wire ranked by need
- Manual refresh of league data
- Multi-tenant safety
- Basic mobile responsiveness (works on a phone, not yet beautiful on one)

**Out (deferred to V1 or later):**
- Yahoo, ESPN, NFL.com
- Draft Room (any kind)
- Trade Evaluator
- Push notifications
- Email notifications other than verification and password reset
- Video and audio
- Mock drafts
- Dynasty-specific tooling
- Custom scoring rule editor
- Write actions to host platform

**MVP timeline (one dev, focused):** ~6–8 weeks from project start. The path is Phase 0 → Phase 1 → minimum of Phase 2 items 2.1–2.4 and 2.8.

---

# Open Phasing Questions

1. **Sleeper-first or Yahoo-first?** Sleeper has no OAuth which makes MVP faster. Yahoo has more users. Recommendation: Sleeper-first, accept that the MVP audience is smaller.
2. **Build Draft Room before or after Trade Evaluator?** Draft Room is more impressive; Trade Evaluator is more useful year-round. Recommendation: Draft Room first because we want it ready before the August draft season.
3. **How much V1 can be shipped before next NFL season?** Hard deadline implied: end of August. Anything later than Phase 4 ships into a quiet market. Plan accordingly.
4. **Should Mock Draft (DR-015) be MVP, V1, or V2?** It is the easiest viral demo and onboards users without requiring a league. Argument for moving it earlier. Recommendation: V1 stretch.

These questions should each become a `design-vote` issue with a recommended option and a deadline.
