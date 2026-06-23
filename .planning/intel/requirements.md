# Requirements Intel
# Sources: PHASES.md (PRD), USER_STORIES.md (PRD)
# Synthesized by gsd-doc-synthesizer

---

## Release Tier Definitions

source: /c/Users/paul_/git/fantasy-football-hub/PHASES.md

MVP — Smallest thing worth using. One person can run their league on it. Target: the two developers plus immediate friends.
V1 — Comfortable sharing publicly. Polish, mobile, real-time. Target: early adopters wanting a Sleeper alternative.
V2 — Differentiating depth. Dynasty tooling, advanced analytics, multi-team trades, mobile PWA. Target: power users and content creators.

---

## MVP Scope (Authoritative Cut)

source: /c/Users/paul_/git/fantasy-football-hub/PHASES.md

In scope for MVP:
- Sign up and sign in (email + Google)
- Connect a Sleeper league
- View league settings, rosters, members
- Team Manager: lineup view, optimal lineup, basic start/sit, waiver wire ranked by need
- Manual refresh of league data
- Multi-tenant safety
- Basic mobile responsiveness (works on phone, not yet polished)

Deferred to V1 or later (explicitly out of MVP):
- Yahoo, ESPN, NFL.com connectors
- Draft Room (any kind)
- Trade Evaluator
- Push notifications
- Email notifications other than verification and password reset
- Video and audio
- Mock drafts
- Dynasty-specific tooling
- Custom scoring rule editor
- Write actions to host platform

MVP timeline: ~6–8 weeks from project start (Phase 0 → Phase 1 → Phase 2 items 2.1–2.4 and 2.8 minimum).

---

## REQ-auth-signup — User Signup with Email

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-001), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.1, 1.2)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Given a new visitor, when they provide email and password, then they receive a verification email and account is created only after verification.
- Email verification and password reset flows are required.
- Phase effort: M (1–3 days)

---

## REQ-auth-google — Google OAuth Sign-In

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-002), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.1)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Given a returning user with a Google identity, when they click "Continue with Google", then they are signed in without entering a password.

---

## REQ-auth-onboarding-nudge — Post-Signup Onboarding

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-003)
tier: MVP (implied — gating behavior for first use)
phase: Phase 1

Acceptance criteria:
- Given a newly signed-up user with no connections, when they land on the dashboard, then they see a clear "Connect your first league" CTA and no other feature is reachable until at least one league is connected.

---

## REQ-lc-sleeper-connect — Connect a Sleeper League

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-001), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (tasks 1.3, 1.4)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Given a new signed-in user with a Sleeper account, when they select "Sleeper" and enter username, then the app fetches leagues without OAuth (read-only public).
- A list of all leagues with name, season, format, and team count is shown.
- The user can select one or more leagues to import.
- Phase effort tasks: 1.3 (S), 1.4 (M)

---

## REQ-lc-yahoo-connect — Connect a Yahoo League via OAuth

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-002), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (tasks 3.1, 3.2)
tier: MVP
phase: Phase 3

Acceptance criteria:
- When user selects "Yahoo", they are redirected to Yahoo OAuth consent page.
- On return, available Yahoo leagues are listed for multi-select import.
- Refresh token is stored encrypted with a per-user envelope key.
- Phase effort: L (3–7 days) each for tasks 3.1 and 3.2.

---

## REQ-lc-espn-private — Connect a Private ESPN League

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-003), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (tasks 3.3, 3.4)
tier: MVP
phase: Phase 3

Acceptance criteria:
- Given a private ESPN league, when user pastes SWID and espn_s2 cookies, app validates against ESPN private endpoint, stores them encrypted, and displays a clear warning that cookies expire.

---

## REQ-lc-espn-public — Connect a Public ESPN League

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-004), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 3.3)
tier: MVP
phase: Phase 3

Acceptance criteria:
- Given a public ESPN league, when user pastes only the league ID, app fetches league metadata without cookies and marks the connection as read-only.

---

## REQ-lc-input-validation — Reject Malformed Connection Input

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-005)
tier: MVP
phase: Phase 1 (Sleeper) / Phase 3 (Yahoo, ESPN)

Acceptance criteria:
- Given invalid league ID, expired cookies, or nonexistent username, user sees a specific human-readable error referencing what to check. No partial connection record is created.

---

## REQ-lc-detect-draft-type — Detect Draft Type on Import

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-010), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.5)
tier: MVP
phase: Phase 1

Acceptance criteria:
- On league import, draft type is classified as one of: snake, auction, linear, third-round reversal.
- Keeper or dynasty flag is set correctly.
- Result shown to user with one-line explanation of how it was inferred.

---

## REQ-lc-detect-scoring — Detect Scoring Rules

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-011), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.5)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Every individual stat-to-point mapping stored in normalized format.
- User can view the full scoring table in a settings panel.
- Any custom or non-standard rule is flagged for verification.

---

## REQ-lc-detect-roster-slots — Detect Roster Slots

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-012), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.5)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Every slot captured with its eligibility list.
- Visual roster shape rendered on the connection summary.

---

## REQ-lc-detect-keeper — Detect Keeper/Dynasty Rules

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-013), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 3.8)
tier: V1
phase: Phase 3

Acceptance criteria:
- Keeper count, cost calculation, and contract years (if dynasty) are captured.
- If any keeper rule is too custom to model, the app reports "unmodeled rule" with a link to add manually.

---

## REQ-lc-connections-list — List All Connections

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-020), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.6)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Given connections across platforms, user sees all grouped by platform with last-sync timestamp and health status.
- Phase effort: S (< 1 day)

---

## REQ-lc-manual-refresh — Refresh League Data on Demand

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-021), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.7)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Clicking "Refresh now" re-pulls settings, rosters, and current matchups from host.
- Stale cache entries are invalidated.
- Refresh completes within 10 seconds for a single league or shows a progress indicator.

---

## REQ-lc-broken-connection — Detect and Surface Broken Connection

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-022), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 3.5)
tier: MVP
phase: Phase 3

Acceptance criteria:
- When scheduled sync detects expired auth, connection is marked unhealthy with reason auth_expired.
- Banner shown on every page until fixed.
- Push notification sent if enabled.

---

## REQ-lc-disconnect — Disconnect a League

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-023)
tier: MVP (implied — connection management)
phase: Phase 1

Acceptance criteria:
- Stored credentials are deleted (not soft-deleted).
- Historical cached data retained for 30 days then purged.
- User asked to confirm before deletion.

---

## REQ-lc-reconnect — Re-connect a Previously Disconnected League

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-024)
tier: MVP (implied)
phase: Phase 1

Acceptance criteria:
- Historical settings or rosters are not silently restored.
- New connection is treated as fresh.

---

## REQ-lc-tenant-isolation — Multi-tenant User Isolation

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-030), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.8)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Each user only sees their own connections.
- Attempt to access another user's league ID returns 404 (not 403, to avoid leaking existence).
- Phase effort: M (1–3 days)

---

## REQ-lc-league-dedup — League Deduplication Across Members

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (LC-031), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 1.11)
tier: MVP
phase: Phase 1

Acceptance criteria:
- Two users in the same Sleeper league each connecting produces one underlying league record (deduped by host_league_id).
- Both users see the same league data but only their own team is highlighted.
- Chat and draft-room participation join the same shared league session.

---

## REQ-tm-optimal-lineup — View Optimal Lineup

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-001), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (tasks 2.2, 2.3)
tier: MVP
phase: Phase 2

Acceptance criteria:
- App displays a recommended starting lineup maximizing projected points within roster eligibility constraints.
- Each starter has a confidence score (0–100).
- Projected point total shown for the lineup.
- Phase effort: 2.2 (L), 2.3 (M)

---

## REQ-tm-lineup-compare — Compare Current vs Optimal Lineup

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-002), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.3)
tier: MVP
phase: Phase 2

Acceptance criteria:
- Current lineup and optimal lineup shown side-by-side.
- Differences highlighted with "Swap suggested" badge.
- Projected delta in points shown.

---

## REQ-tm-push-lineup — Push Lineup to Host Platform

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-003), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.13)
tier: V1
phase: Phase 2

Acceptance criteria:
- Given Yahoo or ESPN connection with write scope, clicking "Apply suggested lineup" submits lineup change via host API.
- Confirmation with new lineup shown.
- If host rejects (locked players, etc.), a specific error is shown.

---

## REQ-tm-manual-override — Manually Override a Recommendation

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-004)
tier: V1 (implied)
phase: Phase 2

Acceptance criteria:
- Dragging a player into a different slot recomputes projected total and confidence.
- Override is remembered for that week even after leaving and returning.

---

## REQ-tm-player-detail — Start/Sit Reasoning per Player

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-010), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.4)
tier: MVP
phase: Phase 2

Acceptance criteria:
- Detail panel shows: projected points, confidence, matchup grade, weather, injury status, opponent rank vs position, recent usage trend.
- A one-paragraph natural-language explanation summarizes the call.
- Phase effort: L (3–7 days)

---

## REQ-tm-player-compare — Compare Two Players Head-to-Head

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-011), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.5)
tier: V1
phase: Phase 2

Acceptance criteria:
- Both players shown in a side-by-side panel.
- Recommended start highlighted with delta and confidence.
- Three biggest factors shown.

---

## REQ-tm-confidence-floor — Confidence Floor Warning

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-012)
tier: V1 (implied)
phase: Phase 2

Acceptance criteria:
- If all flex options have confidence below 55, show a "no strong call" banner instead of a false high-confidence pick.

---

## REQ-tm-injury-status — Real-Time Injury Status

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-020), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.6)
tier: MVP
phase: Phase 2

Acceptance criteria:
- Player downgraded to OUT shows OUT in red.
- Optimizer auto-suggests a replacement.
- Push notification within 5 minutes of source update (if enabled).
- Phase effort: M (1–3 days)

---

## REQ-tm-weather — Weather Impact on Outdoor Games

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-021), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.7)
tier: V1
phase: Phase 2

Acceptance criteria:
- Games with 20+ mph wind, heavy rain, or snow show a weather chip with forecast.
- Projection adjusted down with magnitude shown.
- Indoor stadiums never show weather adjustments.

---

## REQ-tm-game-script — Game Script and Pace Context

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-022)
tier: V1 (implied)
phase: Phase 2

Acceptance criteria:
- RB on a team favored by 10+ shows "Positive game script" as a factor.
- Projection reflects expected workload.

---

## REQ-tm-waiver-wire — Rank Available Waivers by Team Need

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-030), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.8)
tier: MVP
phase: Phase 2

Acceptance criteria:
- Every available player ranked by composite score weighted by team's positional need.
- Re-rankable by raw projection, ownership trend, or breakout score.
- Waiver wire ranks at least 30 viable targets per league (exit criteria).
- Phase effort: L (3–7 days)

---

## REQ-tm-suggested-drop — Suggested Drops for Target Add

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-031), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.9)
tier: MVP
phase: Phase 2

Acceptance criteria:
- Add dialog suggests 1–3 drop candidates ranked by lowest ROS value.
- No suggestions include players locked due to game in progress.

---

## REQ-tm-faab-bid — FAAB Bid Recommendation

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-032), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.10)
tier: V1
phase: Phase 2

Acceptance criteria:
- Recommends bid amount based on remaining budget, target value, and historical similar adds.
- Shows confidence range (e.g. $14 ± $3).

---

## REQ-tm-waiver-type — Detect Waiver Type from League Settings

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-033)
tier: MVP (implied — needed to render correct waiver UI)
phase: Phase 2

Acceptance criteria:
- Rolling waiver priority leagues: FAAB UI hidden, priority order shown instead.

---

## REQ-tm-trend-chart — Per-Player Season Trend Chart

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-040), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.11)
tier: V1
phase: Phase 2

Acceptance criteria:
- Weekly points for current season as a chart.
- Season totals for last 3 seasons.
- Toggle "vs this opponent" to filter.

---

## REQ-tm-news-feed — Player News Feed

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TM-041), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 2.12)
tier: V1
phase: Phase 2

Acceptance criteria:
- News items shown most-recent-first.
- Each item shows source, timestamp, and impact tag (injury, usage, coach quote).

---

## REQ-dr-schedule — Schedule a Draft

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-001), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.1)
tier: V1
phase: Phase 4

Acceptance criteria:
- Commissioner can set date, time, timezone, pick clock, and roster preview window.
- All league members get a calendar invite (ICS) and in-app notification.

---

## REQ-dr-order — Configure Draft Order

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-002), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.1)
tier: V1
phase: Phase 4

Acceptance criteria:
- Commissioner can randomize, manually order, or import draft order from host platform.
- Order is locked when draft starts (configurable).

---

## REQ-dr-rankings-import — Pre-Draft Ranking Import

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-003), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.2)
tier: V1
phase: Phase 4

Acceptance criteria:
- Custom rankings loaded from host platform and editable in a side panel.
- Re-rankable by drag-and-drop with multi-select.

---

## REQ-dr-cheat-sheet — Tiered Cheat Sheets

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-004), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.2)
tier: V1
phase: Phase 4

Acceptance criteria:
- Players grouped into tiers per position.
- Toggle expert sources (ESPN, FantasyPros consensus, our own model).
- Star any player to queue.

---

## REQ-dr-room-ui — Draft Room UI Shell

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-010), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (tasks 4.3, 4.4, 4.5)
tier: V1
phase: Phase 4

Acceptance criteria:
- Bloomberg Terminal aesthetic (DECISION-003, locked): dense data layout with board, best available, roster, queue, chat, alerts simultaneously visible.
- Shows who is on the clock, who is next, and time remaining.
- Live draft board (rounds x teams grid) visible.
- Phase effort: 4.3 (L), 4.4 (M), 4.5 (M)

---

## REQ-dr-on-the-clock — On the Clock Stage

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-011), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.6)
tier: V1
phase: Phase 4

Acceptance criteria:
- Center stage shows team name and logo, large countdown, and queue.
- Desktop and push notification triggered.
- Auto-pick suggestions shown for position of need.

---

## REQ-dr-make-pick — Make a Pick

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-012), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.7)
tier: V1
phase: Phase 4

Acceptance criteria:
- Within 500ms all participants see the pick on the board and a celebratory animation.
- Audio cue plays (configurable mute).
- Next picker announced.

---

## REQ-dr-autopick — Auto-Pick on Timeout

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-013), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.8)
tier: V1
phase: Phase 4

Acceptance criteria:
- Highest-ranked player in queue is auto-drafted on timeout.
- If queue is empty, best available by ADP is taken.
- Pick visually flagged as auto-picked.

---

## REQ-dr-pause — Commissioner Pause/Resume

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-014), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.9)
tier: V1
phase: Phase 4

Acceptance criteria:
- Clock stops for all participants.
- "Draft paused by Commissioner" overlay appears.
- Resume sends a 5-second countdown before clock restarts.

---

## REQ-dr-mock-draft — Mock Draft Mode

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-015), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.13)
tier: V2
phase: Phase 4

Acceptance criteria:
- Solo draft against AI opponents.
- AI uses league-specific rankings and tendencies if available.
- Mock results saved to "Mock history".

---

## REQ-dr-nominate — Auction Nomination

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-020), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 5.1)
tier: V1
phase: Phase 5

Acceptance criteria:
- Player appears on auction stage with starting bid and bid clock when nominated.

---

## REQ-dr-bid — Auction Bidding

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-021), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 5.2)
tier: V1
phase: Phase 5

Acceptance criteria:
- Bid registered atomically.
- All participants see new high bid within 300ms.
- Remaining budget updates.

---

## REQ-dr-auction-win — Win an Auction Lot

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-022), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 5.3)
tier: V1
phase: Phase 5

Acceptance criteria:
- Player added to roster; budget decreases by winning bid; "Sold" animation plays.

---

## REQ-dr-budget-constraint — Budget Constraint Enforcement

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-023), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 5.4)
tier: V1
phase: Phase 5

Acceptance criteria:
- Bid rejected if remaining budget minus bid would leave less than $1 per remaining roster spot.
- Rejection message: "You must reserve $1 per remaining roster spot".

---

## REQ-dr-chat — Draft Room Group Chat

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-030, DR-032), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.10)
tier: V1
phase: Phase 4

Acceptance criteria:
- Messages visible to all participants within 200ms.
- Chat panel scrolls to new message but does not steal focus from board.
- Pre-draft chat history preserved through draft and viewable in post-draft recap.

---

## REQ-dr-reactions — Emoji Reactions to Picks

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-031), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.11)
tier: V1
phase: Phase 4

Acceptance criteria:
- Tapping a pick opens a small emoji set (fire, laugh, skeptical, applause).
- Reactions show as small badges on the pick card.

---

## REQ-dr-video-join — Join Draft Room Video

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-040), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 6.1, 6.2)
tier: V1
phase: Phase 6

Acceptance criteria:
- Camera and microphone permissions requested.
- User joins a WebRTC room.
- Tile appears in video strip.

---

## REQ-dr-audio-only — Audio-Only Draft Join

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-041), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 6.3)
tier: V1
phase: Phase 6

Acceptance criteria:
- Tile shows avatar with active-speaker ring when talking.

---

## REQ-dr-push-to-talk — Push to Talk

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-042), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 6.4)
tier: V2
phase: Phase 6

Acceptance criteria:
- Microphone muted by default; unmuted while holding spacebar (desktop) or button (mobile) when push-to-talk enabled.

---

## REQ-dr-video-failure — Graceful Video Failure

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-043), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 6.5)
tier: V1
phase: Phase 6

Acceptance criteria:
- Draft room continues to function when video drops.
- "Video disconnected — retrying" banner shown.
- Pick clock and chat remain unaffected.

---

## REQ-dr-live-board — Live Draft Board

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-050), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.5)
tier: V1
phase: Phase 4

Acceptance criteria:
- Board grid updates in real time when any pick is made.
- Clicking a pick shows details (when, who suggested it, alternates considered).

---

## REQ-dr-board-filter — Filter the Draft Board

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-051)
tier: V1 (implied)
phase: Phase 4

Acceptance criteria:
- Position filter (e.g. RB only) highlights matching picks and dims others.

---

## REQ-dr-recap — Post-Draft Recap

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (DR-052), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 4.12)
tier: V1
phase: Phase 4

Acceptance criteria:
- Auto-loads after draft ends showing grades per team, value picks, reaches, position-need scores, and full pick log.
- Exportable as shareable image or PDF.
- Phase effort: L (3–7 days)

---

## REQ-te-trade-builder — Start and Build a Trade

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-001, TE-002), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.1)
tier: V1
phase: Phase 7

Acceptance criteria:
- Trade builder opens with both rosters on opposing sides.
- Drag players between offered and requested zones.
- Value summary updates immediately on each change.
- Includes picks, FAAB, future considerations if league supports them.
- Phase effort: L (3–7 days)

---

## REQ-te-submit — Submit a Trade Proposal

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-003), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.2)
tier: V1
phase: Phase 7

Acceptance criteria:
- Proposal sent via in-app notification, email, and (if connected) push to host platform.
- Appears in "Outgoing" list with status pending.

---

## REQ-te-cancel — Cancel an Outgoing Trade

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-004), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.2)
tier: V1
phase: Phase 7

Acceptance criteria:
- Proposal withdrawn, other team notified, status becomes withdrawn.

---

## REQ-te-value-totals — Show Value Totals for Both Sides

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-010), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.3)
tier: V1
phase: Phase 7

Acceptance criteria:
- Total value shown for "What I give" and "What I get".
- Delta shown with a winner indicator.
- Each player has a small bar showing their share of the side's value.
- Layout: decision-tree impact analysis (DECISION-004, locked). Note: PHASES.md task 7.3 references Option A (side-by-side); locked DECISION-004 overrides this to Option C (impact tree). See INFO entry in INGEST-CONFLICTS.md.

---

## REQ-te-value-lenses — Multiple Value Lenses

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-011), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.4)
tier: V1
phase: Phase 7

Acceptance criteria:
- Toggle between: rest-of-season points, dynasty value, playoff schedule, positional scarcity.
- Each lens may produce a different "winner" — intentional.
- Phase effort: L (3–7 days)

---

## REQ-te-roster-impact — Show Roster Impact

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-012), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.5)
tier: V1
phase: Phase 7

Acceptance criteria:
- Projected starting lineup before and after shown for both teams.
- Shows which roster slots become weaker or stronger.
- Phase effort: L (3–7 days)

---

## REQ-te-ai-summary — AI Natural-Language Trade Summary

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-020), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.6)
tier: V1
phase: Phase 7

Acceptance criteria:
- 3–5 sentence summary explaining who wins and why in plain English.
- Summary cites at least two specific factors.
- AI summary under 5 seconds (exit criteria).
- Implementation: Claude API (per PHASES.md task 7.6 reference and ARCHITECTURE.md open question leaning toward Claude/Anthropic).
- Phase effort: L (3–7 days)

---

## REQ-te-hidden-costs — Hidden Cost Flags

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-021), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.7)
tier: V1
phase: Phase 7

Acceptance criteria:
- Each non-obvious cost shown as chip with one-sentence explanation.
- If no flags, panel says "No hidden costs detected".

---

## REQ-te-counter-offer — Counter-Offer Suggestion

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-022), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.8)
tier: V2
phase: Phase 7

Acceptance criteria:
- AI proposes adjusted trade within configurable threshold (default ±5%).
- Presented as a new draft the user can edit.

---

## REQ-te-incoming-notification — Incoming Trade Notification

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-030), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.9)
tier: V1
phase: Phase 7

Acceptance criteria:
- In-app notification, email (if opted in), and push notification (if opted in).
- Appears in "Incoming" list with status pending.

---

## REQ-te-respond — Accept, Reject, or Counter a Trade

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-031), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.10)
tier: V1
phase: Phase 7

Acceptance criteria:
- Incoming trade view shows same evaluation as proposer plus AI analysis from recipient's perspective.
- Can accept, reject (with optional note), or counter.
- Proposer notified within 30 seconds of action.

---

## REQ-te-expiration — Trade Expiration

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-032), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.11)
tier: V1
phase: Phase 7

Acceptance criteria:
- Trade pending beyond configured window (default 48h) auto-rejects with status expired.
- Both parties notified.

---

## REQ-te-history — League Trade History

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-040), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.12)
tier: V2
phase: Phase 7

Acceptance criteria:
- Every completed trade for the season shown with date, parties, and players.
- Retrospective "who actually won" badge based on points scored since trade.

---

## REQ-te-acceptance-patterns — Acceptance Pattern Insights

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-041), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.13)
tier: V2
phase: Phase 7

Acceptance criteria:
- Shows acceptance rate, average response time, and kinds of trades historically accepted.
- If data too sparse, panel says so honestly.

---

## REQ-te-veto-risk — Veto Risk Indicator

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (TE-042), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 7.14)
tier: V2
phase: Phase 7

Acceptance criteria:
- Veto risk indicator based on value delta and historical vetoes in league.
- Hidden in leagues that do not use veto.

---

## REQ-notif-preferences — Notification Preferences

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-010), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.3)
tier: V1
phase: Phase 8

Acceptance criteria:
- User can opt in/out of each category: lineup alerts, injury alerts, trade alerts, draft alerts, weekly recap.
- Channel selectable per category (in-app, email, push).

---

## REQ-notif-quiet-hours — Quiet Hours

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-011), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.3)
tier: V1
phase: Phase 8

Acceptance criteria:
- Push suppressed outside quiet hours (except "always notify" rules); queued for delivery after.

---

## REQ-mobile-draft — Mobile Draft Room Layout

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-020), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.1)
tier: V1
phase: Phase 8

Acceptance criteria:
- Layout collapses to: top header (clock + on-the-clock), middle stage, bottom tab strip for board / queue / chat.
- Video is optional via separate "Tap to join" CTA.

---

## REQ-mobile-lineup — Mobile Lineup Setting

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-021), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.1)
tier: V1
phase: Phase 8

Acceptance criteria:
- Single-column layout with sticky position headers.
- Drag-and-drop works with touch.

---

## REQ-data-readonly-mode — Read-Only Mode When Host Platform Down

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-030), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.9)
tier: V1
phase: Phase 8

Acceptance criteria:
- Cached data shown with "Stale data — host platform down" banner.
- Write actions disabled until host recovers.

---

## REQ-data-eventual-consistency — Eventual Consistency Disclaimer

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md (X-031), /c/Users/paul_/git/fantasy-football-hub/PHASES.md (task 8.9)
tier: V1
phase: Phase 8

Acceptance criteria:
- Before next sync: shows fresh data (if webhook/poll caught) or "Last synced N minutes ago" stamp.

---

## Out of Scope (All Tiers)

source: /c/Users/paul_/git/fantasy-football-hub/USER_STORIES.md

The following are explicitly excluded from all phases:
- Cash dues collection or commissioner payment tools
- League creation (platform hosts the league of record)
- Survivor pools, pick'em, or non-fantasy contests
- Daily Fantasy Sports (DFS) lineup tools
- Player social feed beyond curated news
- Public league discovery / matchmaking
- Mobile native apps (PWA only through V1)
- White-label / multi-tenant beyond per-user isolation
