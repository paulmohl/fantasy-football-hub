# Roadmap: Fantasy Football Hub

## Overview

This roadmap delivers a serious multi-platform fantasy football companion in nine phases (0 through 8 in original numbering, with Phase 0 already complete). Phase 0 laid the technical scaffold. Phases 1 and 2 deliver the MVP: users can sign up, connect a Sleeper league, and get lineup recommendations. Phase 3 extends to Yahoo and ESPN. Phases 4 through 6 build the Draft Room — the marquee feature with a hard August 2026 deadline. Phase 7 delivers the Trade Evaluator. Phase 8 polishes everything for public V1 release. Phase 9 (V2 differentiation) is tracked but not roadmapped here.

## Phases

**Phase Numbering:** Matches original PHASES.md (Phase 0 through Phase 9). Phase 0 is complete. Phase 1 is the current active phase.

- [x] **Phase 0: Project Setup** - Repo, environments, deploy pipeline — COMPLETE
- [ ] **Phase 1: League Connector MVP** - Sign up, connect a Sleeper league, view rosters and settings
- [ ] **Phase 2: Team Manager Core** - Lineup optimization, start/sit recommendations, waiver wire
- [ ] **Phase 3: Multi-Platform Connectors** - Yahoo OAuth and ESPN cookie-based connectors with feature parity
- [ ] **Phase 4: Live Draft Room (Snake)** - Real-time snake draft room with Bloomberg Terminal aesthetic, chat, pick clock
- [ ] **Phase 5: Auction Draft Variant** - Auction nomination, bidding, and budget enforcement inside the draft room
- [ ] **Phase 6: Video and Audio for Draft** - Optional Daily.co video/audio overlay for draft night
- [ ] **Phase 7: Trade Finder and Evaluator** - Two-team trade builder, decision-tree impact analysis, AI natural-language summary
- [ ] **Phase 8: Polish, Mobile, and Notifications** - Mobile layouts, PWA, notification preferences, performance, accessibility, marketing site

## Phase Details

### Phase 0: Project Setup
**Goal**: The technical scaffold exists and every developer can start writing feature code with one command.
**Depends on**: Nothing
**Requirements**: (No REQUIREMENTS.md IDs — infrastructure only)
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts Postgres, Redis, FastAPI app, arq worker, and Vite dev server with no manual steps
  2. FastAPI app and Socket.IO server respond to health checks
  3. Alembic migrations run cleanly on a fresh database
  4. GitHub Actions CI passes (lint, type-check, build) on every PR
  5. App is deployed to the Digital Ocean droplet and reachable over HTTPS
**Plans**: Complete
**Status**: COMPLETE (2026-06-22)

### Phase 1: League Connector MVP
**Goal**: Users can sign up, connect a Sleeper league, and view its settings and rosters — the minimum viable product entry point.
**Depends on**: Phase 0
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, LC-01, LC-02, LC-03, LC-04, LC-05, LC-06, LC-07, LC-08, LC-09, LC-10, LC-11, LC-12
**Success Criteria** (what must be TRUE):
  1. A new visitor can create an account with email/password and complete email verification before gaining access
  2. An existing user with a Google account can sign in without entering a password
  3. A signed-in user can enter a Sleeper username, see their leagues, and import one — including detected draft type, scoring rules, and roster slots — without any OAuth flow
  4. Two users who import the same Sleeper league see the same league data but only their own team highlighted
  5. A user can manually refresh league data, disconnect a league (with confirmation), and re-connect as a fresh import
  6. Attempting to access another user's league returns a 404; the connections list shows only the authenticated user's own leagues
**Plans**: 10 plans
**UI hint**: yes

Plans:
- [ ] 01-01-PLAN.md — Dependencies + docker-compose + PyJWT migration + config extension
- [ ] 01-02-PLAN.md — SQLAlchemy models (User, Session, League, LeagueMember, Team, Roster, AuditLog) + Alembic migration
- [ ] 01-03-PLAN.md — Redis cache helpers (CacheKey, CacheTTL) + FastAPI deps (get_current_user, get_league_for_user) + pytest test infrastructure
- [ ] 01-04-PLAN.md — Email/password auth endpoints (/auth/register, /login, /logout, /refresh, /verify-email, /forgot-password, /reset-password) + /users/me
- [ ] 01-05-PLAN.md — Google OAuth endpoints (/auth/google, /auth/google/callback) using authlib
- [ ] 01-06-PLAN.md — SleeperClient HTTP wrapper + league_service (import_league, refresh_league, classify_draft)
- [ ] 01-07-PLAN.md — Sleeper API proxy routes (/sleeper/lookup, /sleeper/import) + league management routes + arq purge worker + LC test suite
- [ ] 01-08-PLAN.md — Frontend auth foundation: api.ts refresh interceptor, auth store hasLeagues, RequireLeague guard, disabled nav tabs
- [ ] 01-09-PLAN.md — UI component primitives (Button, Input, ChatBubble, TypingIndicator, OptionPill, Toast) + complete LoginPage.tsx
- [ ] 01-10-PLAN.md — ConnectPage.tsx dual-mode (5-step onboarding + My Connections) + supporting components

### Phase 2: Team Manager Core
**Goal**: Once a league is connected, users can view lineup recommendations with reasoning, browse the waiver wire, and inspect player details — read-only, no writes to host yet.
**Depends on**: Phase 1
**Requirements**: TM-01, TM-02, TM-03, TM-04, TM-05, TM-06, TM-07, TM-08, TM-09, TM-10, TM-11, TM-12, TM-13, TM-14, TM-15, TM-16
**Success Criteria** (what must be TRUE):
  1. User can open Team Manager and see a recommended starting lineup with confidence scores and a projected point total
  2. Current lineup and optimal lineup are shown side-by-side with "Swap suggested" badges and a point delta
  3. Clicking any player opens a detail panel with projection, matchup grade, injury status, weather context, and a one-paragraph natural-language explanation of the start/sit call
  4. A player downgraded to OUT appears in red and the optimizer auto-suggests a replacement
  5. The waiver wire shows at least 30 ranked targets weighted by team positional need, re-rankable by multiple criteria
  6. Adding a player shows 1–3 suggested drops ranked by lowest rest-of-season value, with locked players excluded
**Plans**: 12 plans
**UI hint**: yes

Plans:
- [x] 02-01-PLAN.md — Test scaffolding (4 test files + 2 fixture JSONs) + npm install @dnd-kit/core, @dnd-kit/sortable, recharts
- [ ] 02-02-PLAN.md — cache.py extensions + nfl_stadiums.py (32 teams) + ProjectionService (FantasyCalc + Sleeper merge)
- [ ] 02-03-PLAN.md — WeatherService (Open-Meteo + indoor stadium exclusion)
- [ ] 02-04-PLAN.md — LineupOptimizer (greedy slot assignment, confidence scores, OUT replacement)
- [ ] 02-05-PLAN.md — WaiverRanker (dual-mode scoring) + TradeEvaluator (head-to-head comparison)
- [ ] 02-06-PLAN.md — team.py router (5 routes: /my, /lineup, /waiver, /standings, /trade + TM-16 501 stub)
- [ ] 02-07-PLAN.md — league.ts Zustand store + LeagueSwitcher + TeamPage shell with card stack
- [ ] 02-08-PLAN.md — StandingsCard component
- [ ] 02-09-PLAN.md — LineupCard + InjuryBadge + ConfidenceBadge + dnd-kit drag override (TM-15)
- [ ] 02-10-PLAN.md — WaiverCard (dual-mode toggle) + AddPlayerDialog (FAAB/drop candidates)
- [ ] 02-11-PLAN.md — PlayerDetailDrawer + WeatherChip + TrendChart + PlayerComparePanel
- [ ] 02-12-PLAN.md — arq pre-warm task + TM-11 game script flag + TM-12/13 wire-up + TM-14 deferred

### Phase 3: Multi-Platform Connectors
**Goal**: Yahoo and ESPN leagues work end-to-end with the same Team Manager experience as Sleeper.
**Depends on**: Phase 1
**Requirements**: MP-01, MP-02, MP-03, MP-04, MP-05, MP-06, MP-07, MP-08, MP-09
**Success Criteria** (what must be TRUE):
  1. User can connect a Yahoo league via OAuth consent flow; refresh token is stored encrypted; leagues are listed and importable
  2. User can connect a private ESPN league by pasting SWID and espn_s2 cookies, with a clear expiration warning; a public ESPN league connects with only a league ID
  3. Any Yahoo or ESPN league opens in Team Manager with the same lineup, waiver wire, and player detail experience as a Sleeper league
  4. When Yahoo or ESPN credentials expire, a banner appears on every page with a link to re-authenticate — draft room and other features do not crash
  5. Rate limits for each platform are enforced in Redis; the UI shows a soft toast when a limit is hit and serves the cached value
**Plans**: 12 plans
**UI hint**: yes

Plans:
- [ ] 03-01-PLAN.md — DB models (UserCredential, PlayerCrossMap) + Alembic migration 002
- [ ] 03-02-PLAN.md — CredentialService (Fernet encrypt/decrypt/store/rotate per user+platform)
- [ ] 03-03-PLAN.md — YahooClient (OAuth flow, token refresh, Fantasy API endpoints)
- [ ] 03-04-PLAN.md — ESPNClient (cookie-based private auth, unauthenticated public, error handling)
- [ ] 03-05-PLAN.md — yahoo_service (import Yahoo leagues → unified League/Team/Roster models, MP-09 keeper)
- [ ] 03-06-PLAN.md — espn_service (import ESPN leagues → unified models, MP-09 keeper)
- [ ] 03-07-PLAN.md — PlayerCrossMapService (ffb_ids CSV seed, fuzzy fallback, arq weekly refresh)
- [ ] 03-08-PLAN.md — API routes (/auth/yahoo, /auth/yahoo/callback, /espn/connect, /espn/public, /users/me health)
- [ ] 03-09-PLAN.md — Rate limiting (Redis fixed-window, check_platform_rate_limit dependency, X-Rate-Limited header)
- [ ] 03-10-PLAN.md — Expired auth detection (arq health-check task, HealthBanner component, auth store extension)
- [ ] 03-11-PLAN.md — Frontend connect flows (Yahoo OAuth button, ESPN cookie/public forms, PlatformIcon)
- [ ] 03-12-PLAN.md — E2E + integration tests (Playwright ESPN/Yahoo/rate-limit, pytest MP-06/MP-07/MP-09)

### Phase 4: Live Draft Room (Snake)
**Goal**: Any league connected to the Hub can run a real-time snake draft with the Bloomberg Terminal aesthetic — all data visible simultaneously, picks propagating in under 500ms.
**Depends on**: Phase 1
**Requirements**: DR-01, DR-02, DR-03, DR-04, DR-05, DR-06, DR-07, DR-08, DR-09, DR-10, DR-11, DR-12, DR-13, DR-14, DR-15
**Success Criteria** (what must be TRUE):
  1. Commissioner can schedule a draft, set pick clock and draft order, and all league members receive a calendar invite (ICS) and in-app notification
  2. Draft room displays board, best available, roster, queue, chat, and alerts simultaneously in the Bloomberg Terminal dense layout (DECISION-003); pick clock and "on the clock" indicator are always visible
  3. When a pick is made, all participants see it on the board within 500ms; audio cue plays; next picker is announced
  4. On timeout, the highest-ranked queued player is auto-drafted; if queue is empty, best ADP available is taken; pick is flagged as auto-picked
  5. Draft chat messages arrive within 200ms without stealing focus from the board; emoji reactions appear as badges on pick cards
  6. After the draft, a recap page loads automatically with team grades, value picks, reaches, and a full pick log exportable as image or PDF
  7. If a participant disconnects and reconnects, missed events are replayed from the Redis stream; the board state is correct
**Plans**: TBD
**UI hint**: yes

### Phase 5: Auction Draft Variant
**Goal**: Auction drafts run end-to-end inside the same draft room shell — nomination, bidding, budget enforcement, and auction-specific recap.
**Depends on**: Phase 4
**Requirements**: AUC-01, AUC-02, AUC-03, AUC-04, AUC-05
**Success Criteria** (what must be TRUE):
  1. Commissioner can nominate a player; player appears on the auction stage with a starting bid and bid clock visible to all participants
  2. Any participant can place a bid; all participants see the new high bid within 300ms and remaining budget updates in real time
  3. When bidding closes, the winning participant's roster updates, budget decreases by the winning bid, and a "Sold" animation plays
  4. A bid that would leave the bidder with less than $1 per remaining roster spot is rejected with a clear explanation
  5. Post-auction recap shows budget efficiency and dollars per starter for every team
**Plans**: TBD
**UI hint**: yes

### Phase 6: Video and Audio for Draft
**Goal**: League members can optionally join a Daily.co video or audio room during the draft — a bolt-on layer that never degrades the core draft experience if it fails.
**Depends on**: Phase 4
**Requirements**: VA-01, VA-02, VA-03, VA-04
**Success Criteria** (what must be TRUE):
  1. A participant can click "Join video" from inside the draft room; camera/mic permissions are requested; their tile appears in the video strip
  2. A participant can join audio-only; their tile shows an avatar with an active-speaker ring when talking
  3. If video drops during the draft, the board, pick clock, and chat continue to work without interruption; a "Video disconnected — retrying" banner is shown
  4. After the draft ends, the Daily.co room is closed and resources are cleaned up automatically
**Plans**: TBD
**UI hint**: yes

### Phase 7: Trade Finder and Evaluator
**Goal**: Users can propose and evaluate two-team trades with multi-lens value analysis, decision-tree impact visualization, and an AI natural-language summary — and receive and respond to incoming proposals.
**Depends on**: Phase 1
**Requirements**: TE-01, TE-02, TE-03, TE-04, TE-05, TE-06, TE-07, TE-08, TE-09, TE-10, TE-11
**Success Criteria** (what must be TRUE):
  1. User can open the trade builder with both rosters visible, drag players between offered and requested zones, and see value summary update immediately on each change
  2. Trade analysis displays as a decision tree (DECISION-004, locked): starting lineup change, net weekly impact, playoff-week impact, roster shape risk, and dynasty value — with a winner indicator at each node
  3. User can toggle between value lenses (rest-of-season, dynasty, playoff, scarcity); each lens may show a different winner
  4. An AI summary of 3–5 sentences citing at least two specific factors is generated in under 5 seconds
  5. Proposed trade appears in the recipient's incoming list; recipient can accept, reject (with note), or counter; proposer is notified within 30 seconds of action
  6. A trade pending beyond 48 hours auto-rejects with status expired and both parties are notified
**Plans**: TBD
**UI hint**: yes

### Phase 8: Polish, Mobile, and Notifications
**Goal**: The product is ready to share publicly — mobile layouts feel intentional, notifications are configurable, performance is measurable, and a landing page exists.
**Depends on**: Phase 7, Phase 6, Phase 5 (all prior phases complete)
**Requirements**: POL-01, POL-02, POL-03, POL-04, POL-05, POL-06, POL-07, POL-08, POL-09, POL-10
**Success Criteria** (what must be TRUE):
  1. The draft room collapses to a single-column mobile layout with bottom tab strip for board/queue/chat; video is accessible via a separate CTA
  2. Lineup editing on mobile works with touch-based drag-and-drop using pointer events
  3. PWA installs after first successful league connection; cached state is readable offline
  4. Users can configure notification preferences per category and per channel (in-app, email, push) with quiet hours that queue but do not drop notifications
  5. When a host platform is down, cached data is shown with a "Stale data — host platform down" banner; write actions are disabled until host recovers
  6. "Last synced N minutes ago" stamp shown before next sync if a webhook or poll has not yet updated data
  7. WCAG 2.1 AA contrast and keyboard reachability passes on all interactive elements
  8. A public marketing/landing page exists that explains the product and links to sign up
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:** 0 (complete) → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Project Setup | -/- | Complete | 2026-06-22 |
| 1. League Connector MVP | 0/10 | In progress | - |
| 2. Team Manager Core | 1/12 | In progress | - |
| 3. Multi-Platform Connectors | 0/12 | Not started | - |
| 4. Live Draft Room (Snake) | 0/TBD | Not started | - |
| 5. Auction Draft Variant | 0/TBD | Not started | - |
| 6. Video and Audio for Draft | 0/TBD | Not started | - |
| 7. Trade Finder and Evaluator | 0/TBD | Not started | - |
| 8. Polish, Mobile, and Notifications | 0/TBD | Not started | - |
