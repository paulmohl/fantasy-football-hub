# User Stories

All user stories are written in Gherkin (Given / When / Then). Stories are grouped by epic, then by sub-feature. Each story has an ID for cross-referencing in issues, commits, and `PHASES.md`.

## ID Convention

`<EPIC>-<NUMBER>` — `LC-001` is League Connector story 1; `DR-014` is Draft Room story 14.

| Prefix | Epic |
|--------|------|
| `LC` | League Connector |
| `TM` | Team Manager |
| `DR` | Draft Room |
| `TE` | Trade Evaluator |
| `X` | Cross-cutting (auth, mobile, settings, etc.) |

---

# Epic 1 — League Connector

**Goal:** A user can connect any of their fantasy football leagues from a supported host platform in under two minutes, and the app accurately models the league's settings, draft type, scoring, and roster shape.

**Definition of done for the epic:**
- Yahoo, Sleeper, and ESPN are supported in MVP. NFL.com in V1.
- Snake, auction, dynasty, keeper, and superflex variants are detected.
- A user can connect multiple leagues and switch between them without re-authenticating.
- Stored credentials follow the OWASP credential storage cheat sheet (encrypted at rest, refresh-token rotation).

## 1.1 Initial Connection

**LC-001 — Connect a Sleeper league by username**
- **Given** I am a new signed-in user
- **And** I have a Sleeper account with at least one league
- **When** I select "Sleeper" on the Connect page and enter my Sleeper username
- **Then** the app fetches my leagues without requiring OAuth (Sleeper is read-only public)
- **And** I see a list of all leagues with name, season, format, and team count
- **And** I can select one or more leagues to import

**LC-002 — Connect a Yahoo league via OAuth**
- **Given** I am a signed-in user
- **When** I select "Yahoo" on the Connect page
- **Then** I am redirected to Yahoo's OAuth consent page
- **And** when I return, my available Yahoo leagues are listed
- **And** I can multi-select leagues to import
- **And** my refresh token is stored encrypted with a per-user envelope key

**LC-003 — Connect an ESPN league**
- **Given** I am a signed-in user
- **And** my ESPN league is private
- **When** I select "ESPN" and paste my `SWID` and `espn_s2` cookies
- **Then** the app validates the cookies against the ESPN private endpoint
- **And** stores them encrypted
- **And** displays a clear warning that cookies expire and may need refresh

**LC-004 — Connect a public ESPN league with league ID only**
- **Given** my ESPN league is public
- **When** I paste only the league ID
- **Then** the app fetches league metadata without cookies
- **And** marks the connection as read-only

**LC-005 — Reject a malformed connection input**
- **Given** I am on the Connect page
- **When** I enter an invalid league ID, expired cookies, or a username that does not exist
- **Then** I see a specific, human-readable error referencing what to check
- **And** no partial connection record is created in the database

## 1.2 League Settings Detection

**LC-010 — Detect draft type**
- **Given** I have just connected a league
- **When** the app pulls league settings
- **Then** the draft type is correctly classified as one of: snake, auction, linear, third-round reversal
- **And** the keeper or dynasty flag is set correctly
- **And** the result is shown to me with a one-line explanation of how it was inferred

**LC-011 — Detect scoring rules**
- **Given** my league uses half-PPR with a 6-point passing TD rule
- **When** scoring is imported
- **Then** every individual stat-to-point mapping is stored in a normalized format
- **And** I can view the full scoring table in a settings panel
- **And** any custom or non-standard rule is flagged so I know to verify

**LC-012 — Detect roster slots**
- **Given** my league has 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX, 1 SUPERFLEX, 1 K, 1 DST, 6 BN, 1 IR
- **When** the roster format is imported
- **Then** every slot is captured with its eligibility list
- **And** a visual roster shape is rendered on the connection summary

**LC-013 — Detect keeper or dynasty rules**
- **Given** my league has keeper rules
- **When** the app imports settings
- **Then** keeper count, cost calculation, and contract years (if dynasty) are captured
- **And** if any keeper rule is too custom to model, the app reports "unmodeled rule" with a link to add it manually

## 1.3 Connection Management

**LC-020 — List all my connections**
- **Given** I have connected three leagues across two platforms
- **When** I open the Connections page
- **Then** I see all three, grouped by platform, with last-sync timestamp and health status

**LC-021 — Refresh league data on demand**
- **Given** I have a connected league
- **When** I click "Refresh now"
- **Then** the app re-pulls settings, rosters, and current matchups from the host
- **And** stale cache entries are invalidated
- **And** the refresh completes within 10 seconds for a single league or shows a progress indicator

**LC-022 — Detect and surface a broken connection**
- **Given** my ESPN cookies have expired
- **When** a scheduled sync runs
- **Then** the connection is marked `unhealthy` with reason `auth_expired`
- **And** I see a banner on every page until I fix it
- **And** I receive a push notification if I enabled them

**LC-023 — Disconnect a league**
- **Given** I have a connected league
- **When** I select "Disconnect"
- **Then** stored credentials are deleted (not just soft-deleted)
- **And** historical cached data is retained for 30 days then purged
- **And** I am asked to confirm before deletion

**LC-024 — Re-connect a previously disconnected league**
- **Given** I previously connected a league and disconnected it
- **When** I connect it again
- **Then** historical settings or rosters are not silently restored
- **And** the new connection is treated as fresh

## 1.4 Multi-tenant and Sharing

**LC-030 — Each user only sees their own connections**
- **Given** two users on the app, each with leagues
- **When** user A queries any endpoint scoped to a league
- **Then** the response only includes leagues owned by user A
- **And** an attempt to access user B's league ID returns 404, not 403 (to avoid leaking existence)

**LC-031 — Two members of the same league each connect**
- **Given** users A and B are both in the same Sleeper league
- **And** both connect that league to Fantasy Football Hub
- **When** either of them refreshes
- **Then** the underlying league record is shared (deduped by host_league_id)
- **And** both users see the same league data but only their own team is highlighted
- **And** chat and draft-room participation join the same shared league session

---

# Epic 2 — Team Manager

**Goal:** A user can make better weekly lineup decisions, identify the best waiver wire targets, and understand their team's strengths and weaknesses without leaving the app.

## 2.1 Lineup Optimizer

**TM-001 — View this week's optimal lineup**
- **Given** I have a connected league with a roster
- **When** I open my Team Manager for the current week
- **Then** the app displays a recommended starting lineup that maximizes projected points within roster eligibility constraints
- **And** each starter has a confidence score (0–100)
- **And** I can see the projected point total for the lineup

**TM-002 — Compare my current lineup to the optimal**
- **Given** I have set a lineup in the host platform
- **When** I view Team Manager
- **Then** my current lineup and the optimal lineup are shown side-by-side
- **And** any differences are highlighted with a "Swap suggested" badge
- **And** the projected delta in points is shown

**TM-003 — Push lineup changes to the host platform**
- **Given** I have a Yahoo or ESPN connection with write scope
- **When** I click "Apply suggested lineup"
- **Then** the app submits the lineup change via the host API
- **And** I see a confirmation with the new lineup
- **And** if the host rejects the change (locked players, etc.), I see a specific error

**TM-004 — Manually override a recommendation**
- **Given** I see a start/sit suggestion
- **When** I drag a player into a different slot
- **Then** the app recomputes the projected total and confidence
- **And** my override is remembered for this week even if I leave and return

## 2.2 Start/Sit Advisor

**TM-010 — Get start/sit reasoning for any player**
- **Given** I tap on a starter or bench player
- **When** the detail panel opens
- **Then** I see: projected points, confidence, matchup grade, weather, injury status, opponent rank vs position, recent usage trend
- **And** a one-paragraph natural-language explanation summarizing the call

**TM-011 — Compare two players head-to-head**
- **Given** I am deciding between two flex options
- **When** I select "Compare"
- **Then** both players are shown in a side-by-side panel
- **And** the recommended start is highlighted with a delta and confidence
- **And** I see the three biggest factors pushing the recommendation either way

**TM-012 — Confidence floor warning**
- **Given** all my flex options have confidence below 55
- **When** I view the optimizer
- **Then** I see a "no strong call" banner instead of a false high-confidence pick

## 2.3 Injuries, Weather, News

**TM-020 — Real-time injury status**
- **Given** a player on my roster is downgraded to OUT 90 minutes before kickoff
- **When** the app refreshes (auto or manual)
- **Then** the player shows OUT in red
- **And** the optimizer auto-suggests a replacement
- **And** if I have push notifications enabled, I get one within 5 minutes of the source update

**TM-021 — Weather impact on outdoor games**
- **Given** a game has 20+ mph wind, heavy rain, or snow
- **When** I view affected players
- **Then** a weather chip appears with the forecast
- **And** the projection is adjusted down with the magnitude shown
- **And** indoor stadiums never show weather adjustments

**TM-022 — Game script and pace context**
- **Given** my RB is on a team favored by 10+
- **When** I view his card
- **Then** "Positive game script" appears as a factor
- **And** the projection reflects expected workload

## 2.4 Waiver Wire

**TM-030 — Rank available waivers by team need**
- **Given** I am viewing the waiver wire
- **When** the list loads
- **Then** every available player is ranked by a composite score weighted by my team's positional need
- **And** I can re-rank by raw projection, ownership trend, or breakout score

**TM-031 — Suggested drops for a target add**
- **Given** I click "Add" on a waiver target
- **When** the add dialog opens
- **Then** the app suggests 1–3 drop candidates from my roster ranked by lowest rest-of-season value
- **And** none of the suggestions include players locked due to game in progress

**TM-032 — Waiver bid recommendation (FAAB leagues)**
- **Given** my league uses FAAB
- **When** I add a target to my watchlist
- **Then** the app recommends a bid amount based on remaining budget, target value, and historical similar adds
- **And** shows a confidence range (e.g. $14 ± $3)

**TM-033 — Detect waiver type from league settings**
- **Given** my league uses rolling waiver priority (not FAAB)
- **When** the waiver page renders
- **Then** the FAAB UI is hidden and priority order is shown instead

## 2.5 Historical Performance

**TM-040 — Per-player season trend chart**
- **Given** I tap a player from any view
- **When** the player detail page opens
- **Then** I see weekly points for the current season as a chart
- **And** I see season totals for the last 3 seasons
- **And** I can toggle "vs this opponent" to filter

**TM-041 — Player news feed**
- **Given** a player has news in the last 7 days
- **When** I view their detail page
- **Then** news items are shown most-recent-first
- **And** each item shows source, timestamp, and impact tag (e.g. `injury`, `usage`, `coach quote`)

---

# Epic 3 — Live Draft Room

**Goal:** A draft experience that feels like an NFL Draft broadcast — visually immersive, real-time, social, and informative. Every league member can join from any device.

## 3.1 Pre-Draft Setup

**DR-001 — Schedule a draft**
- **Given** I am the league commissioner
- **When** I open Draft Room for an upcoming league
- **Then** I can set a date, time, timezone, pick clock, and roster preview window
- **And** all league members get a calendar invite (ICS) and an in-app notification

**DR-002 — Configure draft order**
- **Given** I am the commissioner
- **When** I open draft settings
- **Then** I can randomize, manually order, or import draft order from the host platform
- **And** the order is locked when the draft starts (configurable)

**DR-003 — Pre-draft ranking import**
- **Given** I have personal rankings on the host platform
- **When** I enter the draft room before draft start
- **Then** my custom rankings are loaded and editable in a side panel
- **And** I can re-rank by drag-and-drop with multi-select

**DR-004 — Tiered cheat sheets**
- **Given** I am on the pre-draft screen
- **When** the cheat sheet loads
- **Then** players are grouped into tiers per position
- **And** I can toggle expert sources (ESPN, FantasyPros consensus, our own model)
- **And** I can star any player to my queue

## 3.2 The Draft Room Experience

**DR-010 — Enter the draft room**
- **Given** the draft is scheduled for now or in the past
- **When** I open the draft room
- **Then** I see the broadcast-style UI: dark, podium aesthetic, large center stage for the active pick
- **And** I see who is on the clock, who is next, and the time remaining
- **And** I see the live draft board (rounds x teams grid) on the side

**DR-011 — On the clock**
- **Given** it is my turn to pick
- **When** my pick window starts
- **Then** the center stage shows my name and team logo, a large countdown, and my queue
- **And** I get a desktop and push notification
- **And** auto-pick suggestions are shown for my position of need

**DR-012 — Make a pick**
- **Given** I am on the clock
- **When** I select a player and confirm
- **Then** within 500ms all participants see the pick on the board and a celebratory animation on stage
- **And** the audio cue plays (configurable mute)
- **And** the next picker is announced

**DR-013 — Auto-pick on timeout**
- **Given** my clock runs out
- **When** the timer hits zero
- **Then** the highest-ranked player in my queue is auto-drafted
- **And** if my queue is empty, the best available by ADP is taken
- **And** the pick is visually flagged as auto-picked

**DR-014 — Pause and resume**
- **Given** the draft is in progress and I am commissioner
- **When** I click "Pause draft"
- **Then** the clock stops for all participants
- **And** a "Draft paused by Commissioner" overlay appears
- **And** resuming sends a 5-second countdown before the clock restarts

**DR-015 — Mock draft mode**
- **Given** I want to practice
- **When** I open mock draft from any league
- **Then** I can solo-draft against AI opponents
- **And** the AI uses league-specific rankings and tendencies if available
- **And** mock results are saved to my "Mock history"

## 3.3 Auction Draft Variant

**DR-020 — Nominate a player**
- **Given** the draft type is auction and I have nomination rights
- **When** I select a player and click "Nominate"
- **Then** the player appears on the auction stage with a starting bid
- **And** the bid clock starts

**DR-021 — Bid on a nominated player**
- **Given** a player is up for auction
- **When** I click "Bid +$1" or enter a custom amount
- **Then** my bid is registered atomically
- **And** all participants see the new high bid within 300ms
- **And** my remaining budget updates

**DR-022 — Win an auction**
- **Given** I have the highest bid when the clock expires
- **When** the timer ends
- **Then** the player is added to my roster
- **And** my budget decreases by the winning bid
- **And** a "Sold" animation plays

**DR-023 — Budget constraint enforcement**
- **Given** I have $5 left and 3 roster spots to fill
- **When** I try to bid $4 on a player
- **Then** the bid is rejected with "You must reserve $1 per remaining roster spot"

## 3.4 Group Chat

**DR-030 — League chat in the draft room**
- **Given** I am in the draft room
- **When** I type in the chat panel and hit enter
- **Then** all participants see my message within 200ms
- **And** the chat panel scrolls to my message but does not steal focus from the board

**DR-031 — Emoji reactions to picks**
- **Given** another team just made a pick
- **When** I tap the pick on the board
- **Then** I can react with a small set of emojis (fire, laugh, skeptical, applause)
- **And** reactions show as small badges on the pick card

**DR-032 — Chat persistence across phases**
- **Given** chat messages were sent during the pre-draft phase
- **When** the draft starts and ends
- **Then** the chat history is preserved and viewable in the post-draft recap

## 3.5 Video and Audio

**DR-040 — Join the league video room**
- **Given** I am in the draft room
- **When** I click "Join video"
- **Then** my camera and microphone permissions are requested
- **And** I join a WebRTC room with other participants
- **And** my tile appears in a video strip along the bottom or side

**DR-041 — Audio-only join**
- **Given** I want to participate verbally but not on camera
- **When** I click "Join audio only"
- **Then** my tile shows my avatar with an active-speaker ring when I talk

**DR-042 — Push to talk option**
- **Given** I am in the video room
- **When** I enable push-to-talk in settings
- **Then** my microphone is muted by default and unmuted while I hold spacebar (desktop) or a button (mobile)

**DR-043 — Graceful video failure**
- **Given** the video service is degraded or my network is poor
- **When** video drops
- **Then** the rest of the draft room continues to function
- **And** I see a "Video disconnected — retrying" banner
- **And** the pick clock and chat remain unaffected

## 3.6 Draft Board and Recap

**DR-050 — Live draft board**
- **Given** I am in the draft room
- **When** any pick is made
- **Then** the draft board grid updates in real time
- **And** I can click any pick to see details (when, who suggested it, alternates considered)

**DR-051 — Filter the board**
- **Given** the draft board is dense
- **When** I select a position filter (RB only)
- **Then** picks for that position are highlighted and others dimmed

**DR-052 — Post-draft recap**
- **Given** the draft just ended
- **When** the recap auto-loads
- **Then** I see grades per team, value picks, reaches, position-need scores, and the full pick log
- **And** I can export the recap as a shareable image or PDF

---

# Epic 4 — Trade Finder & Evaluator

**Goal:** Make trades approachable. Show what each side actually gives up and gets, in terms that align with how leagues argue about value.

## 4.1 Proposing a Trade

**TE-001 — Start a trade with a specific team**
- **Given** I am viewing my league roster
- **When** I click "Propose trade" on another team's name
- **Then** the trade builder opens with my roster on one side and theirs on the other
- **And** I can drag players between the offered and requested zones

**TE-002 — Add or remove players from a trade**
- **Given** I am building a trade
- **When** I drag a player into my "Offering" zone
- **Then** the value summary updates immediately
- **And** I can include picks (for keeper or dynasty), FAAB, or future considerations if my league supports them

**TE-003 — Submit a trade proposal**
- **Given** I have a valid trade builder state
- **When** I click "Send proposal"
- **Then** the proposal is sent to the other team via in-app notification, email, and (if connected) push to the host platform
- **And** the proposal appears in my "Outgoing" trades list with status `pending`

**TE-004 — Cancel an outgoing trade**
- **Given** I have a pending outgoing trade
- **When** I click "Cancel"
- **Then** the proposal is withdrawn, the other team is notified, and status becomes `withdrawn`

## 4.2 Side-by-Side Evaluation

**TE-010 — Show value totals for both sides**
- **Given** I am building or viewing a trade
- **When** the value panel renders
- **Then** I see total value for "What I give" and "What I get"
- **And** the delta is shown with a winner indicator
- **And** each player has a small bar showing their share of the side's value

**TE-011 — Multiple value lenses**
- **Given** I am viewing a trade
- **When** I toggle the value lens
- **Then** I can switch between: rest-of-season points, dynasty value, playoff schedule, positional scarcity
- **And** each lens may produce a different "winner" — that is intentional

**TE-012 — Show roster impact**
- **Given** I am viewing a trade
- **When** I open the impact panel
- **Then** I see my projected starting lineup before and after
- **And** I see the same for the other team
- **And** I see which roster slots become weaker or stronger

## 4.3 AI Analysis

**TE-020 — Natural-language trade summary**
- **Given** I am viewing a trade
- **When** I open the AI analysis panel
- **Then** I see a 3–5 sentence summary explaining who wins and why, in plain English
- **And** the summary cites at least two specific factors (e.g. "Player A has a Week 11–14 playoff schedule against bottom-10 defenses")

**TE-021 — Hidden cost flags**
- **Given** the AI detects a non-obvious cost (giving up the only TE, taking on a bye-week conflict, depth chart risk)
- **When** I view the analysis
- **Then** each flag is shown as a chip with a one-sentence explanation
- **And** if there are no flags, the panel says "No hidden costs detected"

**TE-022 — Counter-offer suggestion**
- **Given** I think a trade is unfair against me
- **When** I click "Suggest counter"
- **Then** the AI proposes an adjusted trade that brings the value within a configurable threshold (default ±5%)
- **And** the suggestion is presented as a new draft I can edit

## 4.4 Notifications and Pending State

**TE-030 — Incoming trade notification**
- **Given** another team sends me a proposal
- **When** the proposal is created
- **Then** I get an in-app notification, email (if opted in), and push notification (if opted in)
- **And** the trade appears in my "Incoming" list with status `pending`

**TE-031 — Accept, reject, or counter**
- **Given** I have an incoming trade
- **When** I open it
- **Then** I see the same evaluation as the proposer plus AI analysis from my side's perspective
- **And** I can accept, reject (with optional note), or counter
- **And** the proposer is notified within 30 seconds of my action

**TE-032 — Trade expiration**
- **Given** a trade has been pending for the configured window (default 48h)
- **When** the window expires
- **Then** the trade auto-rejects with status `expired`
- **And** both parties are notified

## 4.5 History and Patterns

**TE-040 — League trade history**
- **Given** I am viewing my league
- **When** I open the "Trade History" tab
- **Then** I see every completed trade for the season with date, parties, and players
- **And** each trade has a retrospective "who actually won" badge based on points scored since the trade

**TE-041 — Acceptance pattern insights**
- **Given** I have proposed multiple trades to the same team
- **When** I view that team's profile
- **Then** I see their acceptance rate, average response time, and the kinds of trades they have historically accepted
- **And** if patterns are too sparse to be meaningful, the panel says so honestly

**TE-042 — Veto risk indicator (commish-veto leagues only)**
- **Given** my league uses commissioner-veto trades
- **When** I view a pending trade
- **Then** I see a "Veto risk" indicator based on the value delta and historical vetoes in the league
- **And** the indicator is hidden in leagues that do not use veto

---

# Cross-Cutting Stories

## X.1 Authentication and Onboarding

**X-001 — Sign up with email**
- **Given** I am a new visitor
- **When** I provide email and password
- **Then** I receive a verification email
- **And** my account is created only after verification

**X-002 — Sign in with Google**
- **Given** I am a returning user with a Google identity
- **When** I click "Continue with Google"
- **Then** I am signed in without entering a password

**X-003 — Onboarding nudges**
- **Given** I just signed up and have no connections
- **When** I land on the dashboard
- **Then** I see a clear "Connect your first league" CTA
- **And** no other feature is reachable until at least one league is connected

## X.2 Notifications

**X-010 — Notification preferences**
- **Given** I am signed in
- **When** I open notification settings
- **Then** I can opt in or out of each category: lineup alerts, injury alerts, trade alerts, draft alerts, weekly recap
- **And** I can choose channel per category (in-app, email, push)

**X-011 — Quiet hours**
- **Given** I have set quiet hours
- **When** an event would trigger a push outside an explicit "always notify" rule
- **Then** the push is suppressed and queued for after quiet hours

## X.3 Mobile and Responsive

**X-020 — Mobile draft room**
- **Given** I open the draft room on a phone
- **When** the page loads
- **Then** the layout collapses to: top header (clock + on-the-clock), middle stage, bottom tab strip for board / queue / chat
- **And** video is optional and joins via a separate "Tap to join" CTA

**X-021 — Mobile lineup setting**
- **Given** I am on a phone in Team Manager
- **When** I view my lineup
- **Then** the layout is single-column with sticky position headers
- **And** drag-and-drop works with touch

## X.4 Data Integrity

**X-030 — Read-only mode while host platform is down**
- **Given** the host platform is returning 5xx errors
- **When** I open my league
- **Then** I see cached data with a "Stale data — host platform down" banner
- **And** write actions are disabled until the host recovers

**X-031 — Eventual consistency disclaimer**
- **Given** I just made a roster move on the host platform
- **When** I view it in Fantasy Football Hub before the next sync
- **Then** I see either fresh data (because we caught a webhook or polled) or a "Last synced N minutes ago" stamp

---

# Out of Scope (Explicit)

These are things the user might reasonably expect that are **not** in scope for any phase below V2 retrospective. Listed here so they do not creep into MVP.

- Cash dues collection or commissioner payment tools
- League creation (we never host the league of record; users always have a host platform)
- Survivor pools, pick'em, or non-fantasy contests
- Daily Fantasy Sports (DFS) lineup tools
- Player social feed (Twitter aggregation, beat-writer feeds beyond curated news)
- Public league discovery / matchmaking
- Mobile native apps (PWA only through V1)
- White-label / multi-tenant beyond per-user isolation
