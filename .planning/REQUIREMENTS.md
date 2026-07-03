# Requirements: Fantasy Football Hub

**Defined:** 2026-06-22
**Core Value:** Two users can connect a Sleeper league, view rosters, and get lineup recommendations without leaving the Hub.

## v1 Requirements

Requirements committed for Phase 1 through Phase 8. Each maps to exactly one roadmap phase.

### Authentication and Onboarding (Phase 1)

- [ ] **AUTH-01**: User can sign up with email and password; account is created only after email verification
- [ ] **AUTH-02**: User can sign in via Google OAuth without entering a password
- [ ] **AUTH-03**: User can reset a forgotten password via email link
- [ ] **AUTH-04**: A newly signed-up user with no connections sees a "Connect your first league" CTA and cannot reach other features until at least one league is connected

### League Connector — Sleeper (Phase 1)

- [ ] **LC-01**: User can enter a Sleeper username and see a list of their leagues (name, season, format, team count) without OAuth
- [ ] **LC-02**: User can select one or more Sleeper leagues to import (settings, roster format, members)
- [ ] **LC-03**: On import, draft type is classified (snake, auction, linear, third-round reversal) and keeper/dynasty flag is set; result shown with a one-line explanation
- [ ] **LC-04**: Every stat-to-point scoring rule is stored in normalized format; user can view the full scoring table; non-standard rules are flagged
- [ ] **LC-05**: Every roster slot is captured with its eligibility list; visual roster shape is shown on the connection summary
- [ ] **LC-06**: User sees all their connections grouped by platform with last-sync timestamp and health status
- [ ] **LC-07**: User can click "Refresh now" to re-pull settings, rosters, and matchups; completes within 10 seconds or shows a progress indicator
- [ ] **LC-08**: Given invalid input (bad username, expired cookies, nonexistent league ID), user sees a specific human-readable error; no partial connection record is created
- [ ] **LC-09**: Each user sees only their own connections; accessing another user's league ID returns 404
- [ ] **LC-10**: Two users connecting the same Sleeper league produce one underlying league record deduped by host_league_id; both see the same data but only their own team highlighted
- [ ] **LC-11**: User can disconnect a league (credentials deleted, not soft-deleted; historical cached data retained 30 days then purged; user confirms before deletion)
- [ ] **LC-12**: Re-connecting a previously disconnected league is treated as a fresh connection; historical settings are not silently restored

### Team Manager Core (Phase 2)

- [x] **TM-01
**: App displays an optimal starting lineup that maximizes projected points within eligibility constraints; each starter shows a confidence score (0–100) and the projected point total
- [x] **TM-02
**: Current lineup and optimal lineup are shown side-by-side; differences are highlighted with a "Swap suggested" badge and a projected point delta
- [x] **TM-03
**: Per-player detail panel shows: projected points, confidence, matchup grade, weather, injury status, opponent rank vs position, recent usage trend, and a one-paragraph natural-language explanation
- [x] **TM-04
**: Real-time injury status: a player downgraded to OUT shows OUT in red and the optimizer auto-suggests a replacement
- [x] **TM-05
**: Waiver wire ranks every available player by composite score weighted by team positional need; re-rankable by raw projection, ownership trend, or breakout score; at least 30 viable targets per league
- [x] **TM-06
**: Add dialog suggests 1–3 drop candidates ranked by lowest rest-of-season value; no suggestions include players whose game is in progress
- [x] **TM-07
**: App detects waiver type from league settings; FAAB UI is hidden for rolling-priority leagues and priority order is shown instead
- [x] **TM-08
**: User can compare two players head-to-head with recommendation, point delta, confidence, and three biggest factors (V1)
- [x] **TM-09
**: Games with 20+ mph wind, heavy rain, or snow show a weather chip; projection is adjusted down with magnitude shown; indoor stadiums never show weather (V1)
- [x] **TM-10
**: If all flex options have confidence below 55, a "no strong call" banner is shown instead of a false high-confidence pick (V1)
- [x] **TM-11
**: RB on a team favored by 10+ shows "Positive game script" as a factor with projection reflecting expected workload (V1)
- [x] **TM-12
**: FAAB bid recommendation shown with confidence range (e.g., $14 ± $3) for FAAB leagues (V1)
- [x] **TM-13
**: Per-player season trend chart: weekly points for current season, season totals for last 3 seasons, "vs this opponent" toggle (V1)
- [x] **TM-14
**: Player news feed shown most-recent-first with source, timestamp, and impact tag (injury, usage, coach quote) (V1)
- [x] **TM-15
**: User can manually drag a player into a different slot; projected total and confidence recompute; override is remembered for that week (V1)
- [x] **TM-16
**: Given Yahoo or ESPN connection with write scope, user can click "Apply suggested lineup" to submit lineup change via host API; host rejection shows a specific error (V1)

### Multi-Platform Connectors (Phase 3)

- [ ] **MP-01**: User can connect a Yahoo league via OAuth; refresh token stored encrypted; leagues listed for multi-select import
- [ ] **MP-02**: Yahoo leagues, settings, rosters, and scoring are pulled with the same data completeness as Sleeper
- [ ] **MP-03**: User can connect a private ESPN league by pasting SWID and espn_s2 cookies; cookies are stored encrypted with a warning that they expire
- [ ] **MP-04**: User can connect a public ESPN league by pasting only the league ID; connection is marked read-only
- [ ] **MP-05**: ESPN leagues, settings, and rosters are pulled; input validation shows specific errors for expired cookies or bad league IDs
- [ ] **MP-06**: When scheduled sync detects expired auth, connection is marked unhealthy and a banner is shown on every page until fixed
- [ ] **MP-07**: Per-platform rate-limit budgets enforced in Redis; when a user trips a limit the UI shows a soft toast and the cached value is returned
- [ ] **MP-08**: Player IDs are cross-mapped across Yahoo, ESPN, and Sleeper so the same player is a single record
- [ ] **MP-09**: Keeper count, cost calculation, and contract years (dynasty) are captured; unmodeled rules report "unmodeled rule" with a link to add manually (V1)

### Live Draft Room — Snake (Phase 4)

- [x] **DR-01
**: Commissioner can schedule a draft (date, time, timezone, pick clock, roster preview window); all league members receive an ICS calendar invite and in-app notification
- [x] **DR-02
**: Commissioner can randomize, manually order, or import draft order; order is locked when draft starts
- [x] **DR-03
**: User can import custom rankings from host platform and edit in a side panel via drag-and-drop multi-select
- [x] **DR-04
**: Players are grouped into tiered cheat sheets per position; user can toggle expert sources and star players to queue
- [x] **DR-05
**: Draft room shell presents Bloomberg Terminal aesthetic (DECISION-003, locked): draft board, best available, roster, queue, chat, and alerts simultaneously visible; shows who is on the clock, who is next, and time remaining
- [x] **DR-06
**: "On the clock" stage shows team name, large countdown, queue, and auto-pick suggestions; desktop and push notifications are triggered
- [x] **DR-07
**: When a pick is made all participants see it on the board within 500ms; audio cue plays (configurable mute); next picker is announced
- [x] **DR-08
**: On timeout, highest-ranked queued player is auto-drafted; if queue is empty, best available by ADP is taken; pick is flagged as auto-picked
- [x] **DR-09
**: Commissioner can pause the draft (clock stops for all, overlay shown) and resume (5-second countdown before clock restarts)
- [x] **DR-10
**: Draft chat messages are visible to all participants within 200ms; panel scrolls to new message without stealing focus from the board; pre-draft history is preserved through the draft
- [x] **DR-11
**: Tapping a pick opens an emoji reaction set (fire, laugh, skeptical, applause); reactions show as small badges on the pick card
- [x] **DR-12
**: Draft board grid updates in real time for every pick; clicking a pick shows details (when, who suggested it, alternates)
- [x] **DR-13
**: Position filter highlights matching picks and dims others
- [x] **DR-14
**: Post-draft recap auto-loads showing team grades, value picks, reaches, position-need scores, and full pick log; exportable as image or PDF
- [x] **DR-15
**: Real-time infra: Socket.IO + Redis adapter + draft lock (one writer per draft); clients track last event ID and replay missed events on reconnect from Redis stream

### Auction Draft Variant (Phase 5)

- [ ] **AUC-01**: When nomination UI is used, player appears on auction stage with starting bid and bid clock
- [ ] **AUC-02**: Bids are registered atomically; all participants see the new high bid within 300ms; remaining budget updates
- [ ] **AUC-03**: When bidding closes, player is added to winner's roster; budget decreases by winning bid; "Sold" animation plays
- [ ] **AUC-04**: A bid is rejected if remaining budget minus bid would leave less than $1 per remaining roster spot; rejection message explains the rule
- [ ] **AUC-05**: Auction-specific recap shows budget efficiency and dollars per starter

### Video and Audio for Draft (Phase 6)

- [ ] **VA-01**: User can join a Daily.co WebRTC room from inside the draft room; camera and microphone permissions are requested; tile appears in video strip
- [ ] **VA-02**: User can join audio-only; tile shows avatar with active-speaker ring when talking
- [ ] **VA-03**: When video drops, draft room continues to function; "Video disconnected — retrying" banner shown; pick clock and chat are unaffected
- [ ] **VA-04**: Video room is closed and cleaned up after draft ends

### Trade Finder and Evaluator (Phase 7)

- [ ] **TE-01**: Trade builder opens with both rosters on opposing sides; user drags players between offered and requested zones; value summary updates immediately; picks, FAAB, and future considerations included if league supports them
- [ ] **TE-02**: Trade proposal is sent via in-app notification, email, and (if connected) host platform; appears in Outgoing list with status pending
- [ ] **TE-03**: User can cancel an outgoing trade proposal; other team is notified; status becomes withdrawn
- [ ] **TE-04**: Value totals shown for both sides with a delta and winner indicator using decision-tree impact analysis layout (DECISION-004, locked): starting lineup change, net weekly impact, playoff-week impact, roster shape risk, and dynasty value; AI verdict at the bottom
- [ ] **TE-05**: User can toggle between value lenses: rest-of-season points, dynasty value, playoff schedule, positional scarcity; each lens may produce a different winner
- [ ] **TE-06**: Projected starting lineup before and after the trade is shown for both teams; which roster slots become weaker or stronger is highlighted
- [ ] **TE-07**: A 3–5 sentence AI natural-language summary explains who wins and why, citing at least two specific factors; summary completes in under 5 seconds (provisionally Claude API — LLM provider must be voted before Phase 7)
- [ ] **TE-08**: Non-obvious costs shown as chips with one-sentence explanations; if no flags, panel says "No hidden costs detected"
- [ ] **TE-09**: Incoming trade triggers in-app notification, email (if opted in), and push (if opted in); appears in Incoming list with status pending
- [ ] **TE-10**: Incoming trade view shows same evaluation as proposer plus AI analysis from recipient's perspective; user can accept, reject (with optional note), or counter; proposer notified within 30 seconds
- [ ] **TE-11**: Trade pending beyond configured window (default 48h) auto-rejects with status expired; both parties notified

### Polish, Mobile, and Notifications (Phase 8)

- [ ] **POL-01**: Mobile layout for draft room collapses to: top header (clock + on-the-clock), middle stage, bottom tab strip for board/queue/chat; video is optional via "Tap to join" CTA
- [ ] **POL-02**: Mobile lineup setting: single-column layout with sticky position headers; drag-and-drop works with touch (pointer events)
- [ ] **POL-03**: PWA manifest, service worker, and offline read of cached state
- [ ] **POL-04**: User can configure notification preferences per category (lineup alerts, injury, trade, draft, weekly recap) and per channel (in-app, email, push); quiet hours suppress push notifications and queue for delivery
- [ ] **POL-05**: When host platform is down, cached data is shown with a "Stale data — host platform down" banner; write actions are disabled until host recovers
- [ ] **POL-06**: "Last synced N minutes ago" stamp shown before next sync if a webhook or poll has not yet updated data
- [ ] **POL-07**: Performance: query optimization, cache hit-rate dashboard, lazy-loaded routes
- [ ] **POL-08**: Accessibility audit and fixes to WCAG 2.1 AA baseline
- [ ] **POL-09**: Empty states, loading states (skeletons for predictable-shape views; spinners for short indeterminate actions), and error states implemented for every screen
- [ ] **POL-10**: Marketing site / landing page

## v2 Requirements

Deferred to after V1 ships. Not in current roadmap.

### Draft Room V2

- **DR-V2-01**: Mock draft mode — solo draft against AI opponents using league-specific rankings; results saved to Mock history

### Trade Evaluator V2

- **TE-V2-01**: Counter-offer suggestion — AI proposes adjusted trade within ±5% threshold, presented as editable draft
- **TE-V2-02**: League trade history for the season with retrospective "who actually won" badge based on points scored since trade
- **TE-V2-03**: Team trade pattern profile — acceptance rate, average response time, types historically accepted
- **TE-V2-04**: Veto risk indicator based on value delta and historical vetoes; hidden in leagues that do not use veto
- **TE-V2-05**: Multi-team (3+) trade builder

### Platform V2

- **PLAT-V2-01**: NFL.com platform connector
- **PLAT-V2-02**: Dynasty rookie draft support
- **PLAT-V2-03**: League power rankings and weekly recap email
- **PLAT-V2-04**: Public read-only draft recap pages (shareable)
- **PLAT-V2-05**: CLI for power users (terminal-first stats)
- **PLAT-V2-06**: iOS/Android native wrapper (Capacitor or Expo)
- **PLAT-V2-07**: Custom scoring rule editor for unmodeled rules
- **PLAT-V2-08**: Push-to-talk in draft room (hold spacebar / button)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cash dues collection / commissioner payments | Not fantasy tooling; legal complexity |
| League creation | Platform hosts the league of record |
| Survivor pools, pick'em, non-fantasy contests | Different product domain |
| Daily Fantasy Sports (DFS) lineup tools | Different product domain |
| Player social feed beyond curated news | Not core value; scope creep |
| Public league discovery / matchmaking | V2 consideration with additional auth surface |
| White-label / multi-tenant beyond per-user isolation | Not target market |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| LC-01 | Phase 1 | Pending |
| LC-02 | Phase 1 | Pending |
| LC-03 | Phase 1 | Pending |
| LC-04 | Phase 1 | Pending |
| LC-05 | Phase 1 | Pending |
| LC-06 | Phase 1 | Pending |
| LC-07 | Phase 1 | Pending |
| LC-08 | Phase 1 | Pending |
| LC-09 | Phase 1 | Pending |
| LC-10 | Phase 1 | Pending |
| LC-11 | Phase 1 | Pending |
| LC-12 | Phase 1 | Pending |
| TM-01 | Phase 2 | Pending |
| TM-02 | Phase 2 | Pending |
| TM-03 | Phase 2 | Pending |
| TM-04 | Phase 2 | Pending |
| TM-05 | Phase 2 | Pending |
| TM-06 | Phase 2 | Pending |
| TM-07 | Phase 2 | Pending |
| TM-08 | Phase 2 | Pending |
| TM-09 | Phase 2 | Pending |
| TM-10 | Phase 2 | Pending |
| TM-11 | Phase 2 | Pending |
| TM-12 | Phase 2 | Pending |
| TM-13 | Phase 2 | Pending |
| TM-14 | Phase 2 | Pending |
| TM-15 | Phase 2 | Pending |
| TM-16 | Phase 2 | Pending |
| MP-01 | Phase 3 | Pending |
| MP-02 | Phase 3 | Pending |
| MP-03 | Phase 3 | Pending |
| MP-04 | Phase 3 | Pending |
| MP-05 | Phase 3 | Pending |
| MP-06 | Phase 3 | Pending |
| MP-07 | Phase 3 | Pending |
| MP-08 | Phase 3 | Pending |
| MP-09 | Phase 3 | Pending |
| DR-01 | Phase 4 | Pending |
| DR-02 | Phase 4 | Pending |
| DR-03 | Phase 4 | Pending |
| DR-04 | Phase 4 | Pending |
| DR-05 | Phase 4 | Pending |
| DR-06 | Phase 4 | Pending |
| DR-07 | Phase 4 | Pending |
| DR-08 | Phase 4 | Pending |
| DR-09 | Phase 4 | Pending |
| DR-10 | Phase 4 | Pending |
| DR-11 | Phase 4 | Pending |
| DR-12 | Phase 4 | Pending |
| DR-13 | Phase 4 | Pending |
| DR-14 | Phase 4 | Pending |
| DR-15 | Phase 4 | Pending |
| AUC-01 | Phase 5 | Pending |
| AUC-02 | Phase 5 | Pending |
| AUC-03 | Phase 5 | Pending |
| AUC-04 | Phase 5 | Pending |
| AUC-05 | Phase 5 | Pending |
| VA-01 | Phase 6 | Pending |
| VA-02 | Phase 6 | Pending |
| VA-03 | Phase 6 | Pending |
| VA-04 | Phase 6 | Pending |
| TE-01 | Phase 7 | Pending |
| TE-02 | Phase 7 | Pending |
| TE-03 | Phase 7 | Pending |
| TE-04 | Phase 7 | Pending |
| TE-05 | Phase 7 | Pending |
| TE-06 | Phase 7 | Pending |
| TE-07 | Phase 7 | Pending |
| TE-08 | Phase 7 | Pending |
| TE-09 | Phase 7 | Pending |
| TE-10 | Phase 7 | Pending |
| TE-11 | Phase 7 | Pending |
| POL-01 | Phase 8 | Pending |
| POL-02 | Phase 8 | Pending |
| POL-03 | Phase 8 | Pending |
| POL-04 | Phase 8 | Pending |
| POL-05 | Phase 8 | Pending |
| POL-06 | Phase 8 | Pending |
| POL-07 | Phase 8 | Pending |
| POL-08 | Phase 8 | Pending |
| POL-09 | Phase 8 | Pending |
| POL-10 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 80 total
- Mapped to phases: 80
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-06-22 after initial project initialization*
