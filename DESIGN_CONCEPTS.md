# Design Concepts

This document presents three distinct UI directions for each of the four primary screens. Each concept is intended to feel cohesive on its own — you should be able to pick one direction per screen, but be aware that a unified app will feel best if at least the major decisions are consistent across screens.

All wireframes are ASCII. Imagery and final visual treatment will be decided in a later pass; the goal here is **layout, density, and information hierarchy**, not pixel-perfect aesthetics.

**How to vote:** For each screen, three options are presented (A, B, C). Open a `design-vote` issue per screen with the three options pasted in. React on the option you prefer. Soft vetoes welcome — leave a comment.

**Shared design tokens (proposed):**

| Token | Value |
|-------|-------|
| Background (dark) | `#0B0E14` (near-black, very slight blue) |
| Surface | `#141822` |
| Surface elevated | `#1B2030` |
| Primary accent | `#3DA9FC` (electric blue) — used sparingly |
| Success | `#5CC8A9` |
| Warning | `#F2B66D` |
| Danger | `#F26D6D` |
| Text primary | `#E8ECF1` |
| Text secondary | `#9AA3B2` |
| Border | `#262C3A` |
| Font | Inter (UI), JetBrains Mono (data tables) |

The dark palette is the default. A light palette will be derived in V1. Draft Room is always dark regardless of user preference (broadcast aesthetic).

---

# Screen 1 — League Connector Onboarding

The first impression. A new user lands here right after signing up. They have zero connected leagues. The job: get them connected in under two minutes without making the app feel intimidating.

## Option A — Platform-First Wizard

A single, focused, multi-step wizard. One decision per screen. Best for users who do not know what they need.

```
+--------------------------------------------------------------+
|  Fantasy Football Hub                              [P] Paul  |
+--------------------------------------------------------------+
|                                                              |
|              Step 1 of 3 -- Pick your platform               |
|                                                              |
|   +----------+   +----------+   +----------+   +----------+ |
|   |          |   |          |   |          |   |          | |
|   |  Yahoo   |   | Sleeper  |   |  ESPN    |   | NFL.com  | |
|   |          |   |          |   |          |   |          | |
|   |  OAuth   |   | Username |   | Cookies  |   |  OAuth   | |
|   +----------+   +----------+   +----------+   +----------+ |
|                                                              |
|                                                              |
|   "Not sure which one? Pick the platform your league is on.  |
|    You can connect multiple later."                          |
|                                                              |
|                                              [Back]  [Next]  |
+--------------------------------------------------------------+
```

```
+--------------------------------------------------------------+
|              Step 2 of 3 -- Enter your username              |
|                                                              |
|   Sleeper username                                           |
|   +--------------------------------------------------+       |
|   | _________________________________________________|       |
|   +--------------------------------------------------+       |
|                                                              |
|   We will pull your public leagues. No password needed.      |
|                                                              |
|                                              [Back]  [Find]  |
+--------------------------------------------------------------+
```

```
+--------------------------------------------------------------+
|         Step 3 of 3 -- Pick the leagues to import            |
|                                                              |
|   [x] Dynasty Kings 2025 - 12 teams - Dynasty - 1QB         |
|   [x] Mom's Money League - 10 teams - Redraft - PPR         |
|   [ ] Work Survivor Pool - not a fantasy league             |
|                                                              |
|                                            [Back]  [Import]  |
+--------------------------------------------------------------+
```

**Pros:** Friendly. No cognitive load. Forgiving.
**Cons:** Three screens for what could be one. Power users will find it slow.

## Option B — Single-Page Form with Inline Help

Everything on one page. Platform pills at the top swap out the input form below. Best for users who know what they want.

```
+--------------------------------------------------------------+
|  Connect a league                                  [P] Paul  |
+--------------------------------------------------------------+
|                                                              |
|   ( Yahoo )  ( Sleeper )  ( ESPN )  ( NFL.com )             |
|                                                              |
|   +--- Sleeper -------------------------------------------+ |
|   |                                                       | |
|   |  Username                                             | |
|   |  +-------------------------------------------------+  | |
|   |  | paulmohl                                        |  | |
|   |  +-------------------------------------------------+  | |
|   |                                                       | |
|   |  > "Public, no password. We will list your leagues   | |
|   |     and you pick which to import."                   | |
|   |                                                       | |
|   |                                          [Find leagues] |
|   +-------------------------------------------------------+ |
|                                                              |
|   +--- Your leagues (will appear here) -------------------+ |
|   |                                                       | |
|   |  (empty)                                              | |
|   +-------------------------------------------------------+ |
|                                                              |
+--------------------------------------------------------------+
```

After "Find leagues":

```
   +--- Your leagues -------------------------------------+
   | [x] Dynasty Kings 2025 - 12 teams - Dynasty - 1QB    |
   | [x] Mom's Money League - 10 teams - Redraft - PPR    |
   | [ ] Work Survivor Pool                               |
   |                                                       |
   |                                          [Import 2]   |
   +-------------------------------------------------------+
```

**Pros:** Fast. Visible context. Easy to add multiple later.
**Cons:** First-time users see more at once. Tab metaphor (pills) needs to be unmistakable.

## Option C — Conversational

A dedicated full-height onboarding chat that asks one thing at a time. Casual tone. Best for users who want something to feel modern.

```
+--------------------------------------------------------------+
|                Fantasy Football Hub onboarding               |
+--------------------------------------------------------------+
|                                                              |
|   FFH:  Welcome! Which platform is your league on?           |
|         [Yahoo] [Sleeper] [ESPN] [NFL.com] [Other]           |
|                                                              |
|   YOU:  Sleeper                                              |
|                                                              |
|   FFH:  Cool. What is your Sleeper username?                 |
|                                                              |
|   YOU:  paulmohl                                             |
|                                                              |
|   FFH:  Found 3 leagues. Pick the ones to import.            |
|                                                              |
|         [x] Dynasty Kings 2025                               |
|         [x] Mom's Money League                               |
|         [ ] Work Survivor Pool                               |
|                                                              |
|                                              [Import these]  |
|                                                              |
+--------------------------------------------------------------+
```

**Pros:** Approachable. Differentiated from competitors. Easy to extend with help replies.
**Cons:** Slower than a single form. Conversational UIs can age poorly if overused. Not great for re-connect flows.

**Recommendation:** **B (Single-page form)** for the long term. **A (Wizard)** acceptable for MVP if it ships faster. **C (Conversational)** is fun but probably better reserved for an optional "Help me decide" entry point rather than the default flow.

---

# Screen 2 — Team Manager Dashboard

The most-visited screen during the season. The user's home for their team. Must surface what matters this week without burying anything important.

## Option A — Information-Dense Single View

Everything on one screen. Lineup left, suggestions middle, news/waiver right. Optimized for the user who lives here.

```
+----------------------------------------------------------------------+
|  Team: Berserkers     League: Dynasty Kings 2025     Week 7   <  >   |
+----------------------------------------------------------------------+
| MY LINEUP            | RECOMMENDATIONS         | NEWS & WAIVERS      |
|----------------------|-------------------------|---------------------|
| QB  Mahomes  21.4    | START Mahomes (94)      | NEWS                |
|  RB Bijan    14.2  v |  > vs ARI, 65F dome     |                     |
|  RB Saquon   16.1  ^ | START Bijan (88)        | A.Gibbs limited     |
|  WR JJ       13.8    |  > matchup grade A      | (Wed practice)      |
|  WR Lamb     12.7    | START Saquon (91)       |                     |
|  WR Olave     8.4  ! |  > positive game script | Chase trending up   |
|  TE Andrews  10.1    | START JJ (87)           | (target share +6%)  |
|  FLEX Kupp   11.0    | SIT  Olave (52)         |                     |
|  K   Bass     8.0    |  > QB downgrade         |---------------------|
|  DST 49ers    9.5    | SWAP Olave -> Pittman   | WAIVER TARGETS      |
|                      |  > +3.1 projected pts   |                     |
|                      |  > [Apply swap]         | 1. Pittman  bid $14 |
| ---- Bench -----     |                         | 2. Spears   bid $9  |
| Pittman   12.1 ↑     |-------------------------| 3. Skyy     bid $5  |
| Spears     8.4       | PROJECTED: 145.2        |                     |
| White      0.0 IR    | OPTIMAL:   148.3        | [See all]           |
|                      | DELTA:    +3.1          |                     |
+----------------------------------------------------------------------+
```

**Pros:** Power-user efficient. Everything visible at once. Mirrors `fantasybbleague`'s direct style.
**Cons:** Dense on mobile (must collapse to tabs). New users may not know where to look first.

## Option B — Card-Based, Scannable

A vertical stack of focused cards. Each card answers one question. Designed for thumb-scroll on mobile, comfortable on desktop.

```
+----------------------------------------------------------------------+
|  Berserkers - Week 7                                  <  Week 7  >   |
+----------------------------------------------------------------------+
|                                                                      |
|  +-- THIS WEEK ---------------------------------------------+        |
|  |  Projected   148.3   vs Opponent: 132.1    Win prob 64%  |        |
|  |  [View lineup]                                            |        |
|  +-----------------------------------------------------------+        |
|                                                                      |
|  +-- ACTION ITEMS (3) -----------------------------------+           |
|  |                                                       |           |
|  |  !  Olave -> Pittman swap (+3.1 pts)     [Apply]    |           |
|  |  !  A.Gibbs limited practice (info)       [Read]     |           |
|  |  ?  Strong waiver target: Pittman         [Bid $14]  |           |
|  +-------------------------------------------------------+           |
|                                                                      |
|  +-- LINEUP ---------------------------------------------+           |
|  |  QB    RB    RB    WR    WR    WR    TE    FLEX  K  DST          |
|  |  Mah   Bij   Saq   JJ    Lam   Ola   And   Kupp  Bas  49ers      |
|  |  21    14    16    14    13    8     10    11    8   10          |
|  |                                                [Edit] |           |
|  +-------------------------------------------------------+           |
|                                                                      |
|  +-- BENCH AND IR -------------------------------------+             |
|  |  Pittman 12 ↑   Spears 8   White IR                |             |
|  +-----------------------------------------------------+             |
|                                                                      |
|  +-- WAIVER WIRE TOP 5 ----------------------------+                 |
|  |  Pittman, Spears, Skyy, Hill, Hunter            |                 |
|  +--------------------------------------------------+                |
|                                                                      |
+----------------------------------------------------------------------+
```

**Pros:** Scannable. Excellent on mobile. Friendly to new users.
**Cons:** Requires more scrolling on desktop. Power users may feel slowed.

## Option C — Split: Strategy Top, Execution Bottom

Top half: insight ("what should I do"). Bottom half: roster ("here is my team"). Clear mental model: read top, act bottom.

```
+----------------------------------------------------------------------+
|  Berserkers - Week 7                                 <  Week 7  >    |
+----------------------------------------------------------------------+
| STRATEGY VIEW                                                        |
|                                                                      |
|    Projected lineup: 148.3       Opp: 132.1       Win prob: 64%      |
|                                                                      |
|    +-- The 3 calls that matter this week -------------------+        |
|    |                                                         |        |
|    |  1. Swap Olave -> Pittman  (+3.1)                       |        |
|    |     "Olave's QB is downgraded; Pittman has volume edge" |        |
|    |                                                         |        |
|    |  2. Monitor Gibbs (limited practice)                    |        |
|    |     "Recheck Friday. Likely active."                    |        |
|    |                                                         |        |
|    |  3. Bid Pittman ($14 of $52 FAAB)                       |        |
|    |     "High-confidence breakout; thin WR room"            |        |
|    +---------------------------------------------------------+        |
|                                                                      |
+----------------------------------------------------------------------+
| ROSTER                                                               |
|                                                                      |
|  QB  Mahomes   21.4     BENCH   Pittman   12.1    IR   White         |
|  RB  Bijan     14.2             Spears     8.4                       |
|  RB  Saquon    16.1                                                  |
|  WR  JJ        13.8     [Drag to reorder] [Apply optimal lineup]     |
|  WR  Lamb      12.7                                                  |
|  WR  Olave      8.4     ! suggested swap                            |
|  TE  Andrews   10.1                                                  |
|  FLX Kupp      11.0                                                  |
|  K   Bass       8.0                                                  |
|  DST 49ers      9.5                                                  |
+----------------------------------------------------------------------+
```

**Pros:** Strongest narrative. New users immediately know what to do. Pairs well with a confidence-scored coach voice.
**Cons:** Some screen real estate spent on the narrative section that experts will skip.

**Recommendation:** **C (Split)** as the primary direction with a hidden "compact" toggle that switches to **A** for power users. **B** is excellent for mobile and should drive the mobile layout regardless of which desktop direction we pick.

---

# Screen 3 — Live Draft Room

The marquee feature. Must feel different from the rest of the app — broadcast, dramatic, dark. This is where we earn the right to call ourselves a serious fantasy app.

## Option A — Broadcast Stage (Center Spotlight)

A central "stage" dominates. The current pick is theatrical. The board, queue, and chat are in supporting panes.

```
+---------------------------------------------------------------------------+
|  ROUND 4 - PICK 39 OVERALL                              CLOCK  00:47 ▼    |
+---------------------------------------------------------------------------+
|                                                                           |
|   [BOARD] [QUEUE] [CHAT]                                                  |
|                                                                           |
|   +----------- DRAFT BOARD (R1-R4) -----------+                          |
|   | R1: A B C D E F G H I J K L              |                          |
|   | R2: L K J I H G F E D C B A              |                          |
|   | R3: A B C D E F G H I J K L              |                          |
|   | R4: L K J I H G [*] _ _ _ _ _            |   ON THE CLOCK            |
|   +-------------------------------------------+                          |
|                                                                           |
|                                                +-------------------+      |
|                                                |                   |      |
|                                                |    BERSERKERS     |      |
|                                                |     (You)         |      |
|                                                |                   |      |
|                                                |   Pick in 00:47   |      |
|                                                |                   |      |
|                                                |   Suggested:      |      |
|                                                |   1. Saquon       |      |
|                                                |   2. Lamb         |      |
|                                                |   3. Andrews      |      |
|                                                |                   |      |
|                                                |   [DRAFT SAQUON]  |      |
|                                                +-------------------+      |
|                                                                           |
|   +--- CHAT (last 3) -------+    +--- VIDEO (4 of 12 live) ---+         |
|   | Marc: lol Andrews again |    | [Marc] [Joe] [Anna] [Sam] |         |
|   | Joe:  trade me Bijan    |    |  [Join video]              |         |
|   | You:  no                |    +----------------------------+         |
|   +-------------------------+                                            |
+---------------------------------------------------------------------------+
```

**Pros:** Cinematic. Differentiated. Best emotional payoff when it's your pick.
**Cons:** Off-the-clock periods can feel passive. Mobile adaptation requires more thought.

## Option B — Bloomberg Terminal for Drafts

High information density. The draft is a fast-moving data stream and we treat it like one. Designed for the drafter who already knows what they want.

```
+---------------------------------------------------------------------------+
| R4P39  CLK 00:47  ON: Berserkers       NEXT: Wolves, Sharks, Tigers       |
+---------------------------------------------------------------------------+
| BOARD                            | BEST AVAILABLE                         |
| R1 ...........................   | 1  RB  Saquon B    NYG   ADP 35       |
| R2 ...........................   | 2  WR  Lamb        DAL   ADP 36       |
| R3 ...........................   | 3  TE  Andrews     BAL   ADP 41       |
| R4 ......[ ]...............      | 4  WR  Diggs       HOU   ADP 44       |
|                                  | 5  RB  Achane      MIA   ADP 47       |
| MY ROSTER                        | 6  ...                                 |
| QB Mahomes  RB Bijan             |                                        |
| RB ____      WR JJ                | QUEUE (mine)                          |
| WR ____      TE ____              | [1] Saquon  [2] Lamb  [3] Andrews    |
|                                  |                                        |
| ALERTS                           | CHAT                                   |
| Andrews falling (-3 spots)       | Marc: snipe lamb                       |
| Saquon high value at 39          | Joe : take Andrews                     |
|                                  | You : ...                              |
+---------------------------------------------------------------------------+
| [Draft Saquon]  [Draft Lamb]  [Draft Andrews]  [Pick from list]  [Queue]  |
+---------------------------------------------------------------------------+
```

**Pros:** Maximum info per pixel. Power-user gold. Looks unlike any other fantasy app.
**Cons:** Less broadcast feel. Intimidating for new drafters. Harder to make beautiful.

## Option C — Hybrid: Stage on Your Pick, Terminal Otherwise

When it is *your* pick, the layout transitions into broadcast mode (Option A). When it is anyone else's, the layout is the dense terminal (Option B). State-driven, animated transition.

```
NOT YOUR PICK:
+---------------------------------------------------------------------------+
| R4P38  CLK 00:21  ON: Wolves (Marc)        NEXT: Berserkers (YOU)         |
+---------------------------------------------------------------------------+
| ROSTER  BOARD  BEST-AVAIL  QUEUE  CHAT  (all visible, compact)            |
+---------------------------------------------------------------------------+

YOUR PICK (transitions in over 0.5s):
+---------------------------------------------------------------------------+
| R4P39  ON THE CLOCK                                          CLOCK 00:47  |
+---------------------------------------------------------------------------+
|                                                                           |
|                    +-----------------------------+                        |
|                    |                             |                        |
|                    |       BERSERKERS            |                        |
|                    |        (You)                |                        |
|                    |                             |                        |
|                    |   Pick in 00:47             |                        |
|                    |   Suggested: Saquon Barkley |                        |
|                    |                             |                        |
|                    |     [DRAFT SAQUON]          |                        |
|                    |     [pick someone else]     |                        |
|                    +-----------------------------+                        |
|                                                                           |
| Board / Queue / Chat / Video tucked into bottom strip, expandable.        |
+---------------------------------------------------------------------------+
```

**Pros:** Best of both. Drama when it matters; density the rest of the time.
**Cons:** Most engineering effort. Two layouts to maintain. Transitions must feel right.

**Recommendation:** **C (Hybrid)** if we are willing to invest in animation polish. Otherwise **A (Broadcast)** because the emotional payoff of "you are on the clock" is the single most memorable moment of draft night and we should prioritize it.

---

# Screen 4 — Trade Evaluator

The trade builder + evaluator. Must show value, intent, and impact clearly. Should never feel like the app is judging you — show the math, let the user decide.

## Option A — Side-by-Side Mirror

Two equal columns: "you give" left, "you get" right. Value totals at the bottom. Analysis below.

```
+----------------------------------------------------------------------+
|  Trade: Berserkers <-> Wolves                            [Send]  X   |
+----------------------------------------------------------------------+
|                                                                      |
|   YOU GIVE                          |   YOU GET                      |
|   ----------                        |   ---------                    |
|   [+] Add player                    |   [+] Add player               |
|                                     |                                |
|   Saquon Barkley   RB   45.2 val    |   Justin Jefferson  WR  62.1   |
|   AJ Brown         WR   33.1 val    |                                |
|   2026 3rd-round pick   ~5.0 val    |                                |
|                                     |                                |
|   --------------------              |   --------------------         |
|   Total: 83.3                       |   Total: 62.1                  |
|                                     |                                |
|   DELTA: -21.2  (you give more)                                     |
|                                                                      |
+----------------------------------------------------------------------+
|  ANALYSIS                                                            |
|                                                                      |
|  AI verdict: Wolves win this trade by 21 points of ROS value.        |
|                                                                      |
|  > Jefferson is elite but Saquon + AJ Brown is two starters.         |
|  > Your RB depth becomes the team weakness post-trade.               |
|  > Wolves' RB room was already deep; this is a value play for them.  |
|                                                                      |
|  Hidden costs:                                                       |
|  - You drop your WR2 and lose a flex flex starter                    |
|  - Wolves get a clear RB1 vs your hole at RB                         |
|                                                                      |
|  [Suggest counter]   [Send anyway]   [Cancel]                        |
+----------------------------------------------------------------------+
```

**Pros:** Symmetric. Easy to read. Math is right where you expect it.
**Cons:** Two-team only. Multi-team trades (V2) need a different layout.

## Option B — Scale of Justice

A visual balance bar. The trade tilts left or right. Drag players in; the scale animates.

```
+----------------------------------------------------------------------+
|  Trade Builder                                            [Send]  X  |
+----------------------------------------------------------------------+
|                                                                      |
|              You             |             Them                      |
|              ---             |             ----                      |
|                                                                      |
|         Saquon, AJ Brown,    |         Justin Jefferson              |
|         2026 3rd pick        |                                       |
|                                                                      |
|    -------+-------+-------+--+--+-------+-------+-------              |
|           |       |       |     |       |       |                    |
|    -25%   -15%   -5%      ↓     +5%    +15%    +25%                  |
|                                                                      |
|                       SCALE TILT: -25%                              |
|                       (you give 25% more)                            |
|                                                                      |
|  +-- Value lens --+                                                  |
|  | (•) ROS pts    |                                                  |
|  | ( ) Dynasty    |                                                  |
|  | ( ) Playoff    |                                                  |
|  | ( ) Scarcity   |                                                  |
|  +----------------+                                                  |
|                                                                      |
|  AI: "This trade is heavily in Wolves' favor on ROS points.          |
|       It is closer (-12%) on dynasty value because Jefferson is      |
|       younger than both of your assets combined."                    |
|                                                                      |
|  [Suggest counter]   [Send]   [Cancel]                               |
+----------------------------------------------------------------------+
```

**Pros:** Visceral. The metaphor is instantly readable. Emotional design.
**Cons:** The scale can feel cute or imprecise. Numbers still need to be visible somewhere.

## Option C — Decision-Tree Analysis View

The trade is presented as a small decision tree of consequences. The builder is collapsed into a header. The body is dedicated to "what does this actually do to my season."

```
+----------------------------------------------------------------------+
|  Trade summary:                                          [Send]  X   |
|  You give: Saquon, AJ Brown, 2026 3rd                                |
|  You get:  Justin Jefferson                                          |
+----------------------------------------------------------------------+
|                                                                      |
|  IMPACT TREE                                                         |
|                                                                      |
|  Starting lineup change                                              |
|   |-- WR1 upgrade: AJ Brown -> Jefferson  +4.8 pts/week              |
|   |-- WR2 downgrade: depth fills in       -2.1 pts/week              |
|   `-- RB FLEX downgrade: Saquon -> Spears -3.4 pts/week              |
|                                                                      |
|  Net weekly impact:  -0.7 pts/week  (-12.6 ROS)                      |
|                                                                      |
|  Playoff weeks (15-17)                                               |
|   |-- Net impact:  -2.1 pts/week                                     |
|   `-- Why: Saquon has 2 easy matchups in those weeks                 |
|                                                                      |
|  Roster shape risk                                                   |
|   |-- RB depth chart goes from B+ to D                               |
|   `-- One injury away from FLEX hole                                 |
|                                                                      |
|  Dynasty value (2026+)                                               |
|   `-- Slight gain (+8%) -- Jefferson is younger                      |
|                                                                      |
|  +-- AI verdict ------------------------------+                      |
|  | Reject for redraft. Lean accept for dynasty|                      |
|  | unless you can solve RB depth elsewhere.   |                      |
|  +--------------------------------------------+                      |
|                                                                      |
|  [Modify trade]   [Send]   [Counter]   [Reject]                      |
+----------------------------------------------------------------------+
```

**Pros:** Most decision-useful. Treats the user as smart. Differentiated.
**Cons:** Heavier engineering. Less viscerally satisfying than Option B. May intimidate first-time trade proposers.

**Recommendation:** **A (Side-by-side)** for MVP because it is the lowest-risk build and matches user expectations from other apps. **C (Impact tree)** as the V1 upgrade once we have confident roster-impact modeling. **B (Scale)** is fun but probably better as a small embedded widget inside another layout, not the primary view.

---

# Cross-Screen Decisions

A few decisions are not screen-specific but shape every screen.

### Navigation Pattern

Three options:

- **A. Top nav** — horizontal bar across the top. Familiar. Works on desktop, collapses to hamburger on mobile.
- **B. Side rail** — fixed left rail with icons + labels on hover. More vertical screen real estate.
- **C. Bottom tab bar (mobile) + top nav (desktop)** — best mobile pattern; pairs with top nav on desktop.

**Recommendation:** **C.** Mobile uses bottom tabs (home, team, league, draft, more), desktop uses a left rail. Draft Room overrides navigation entirely (full-screen broadcast mode).

### Empty States

For every screen, an explicit empty-state design is required. Examples:

- League Connector with no leagues → big CTA, no skeletons
- Team Manager mid-week with no recommendations yet → "Recommendations will appear by Wednesday"
- Trade Evaluator with no trades → list of suggested trade partners ("These teams need RB help")

Empty states should never look like errors.

### Loading States

We prefer **skeletons** over spinners for any view that has a predictable shape (rosters, lineups, draft board). Spinners only for short, indeterminate actions (sending a trade, applying a lineup).

### Toasts and Alerts

- **Toasts**: ephemeral, non-blocking, top-right. 4-second auto-dismiss for info; sticky for errors.
- **Modal alerts**: only for confirmations and destructive actions.
- **Banners**: persistent, at top of relevant page, for state that the user must act on (broken connection, stale data).

### Iconography

Lucide React for line icons. Sport-specific glyphs (helmet, football) custom SVG.

### Accessibility Baseline

- WCAG 2.1 AA contrast on all text
- Every interactive element keyboard-reachable
- ARIA labels on icon-only buttons
- Focus traps in modals
- Reduced-motion media query honored (auto-pick animations, draft-stage transitions become instant)
