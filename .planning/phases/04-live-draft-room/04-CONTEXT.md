---
phase: 4
phase_name: Live Draft Room (Snake)
status: decisions-recorded
created: 2026-06-30
source: discuss-phase interactive session with Paul
---

# Phase 4 Context — Live Draft Room (Snake)

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers a real-time snake draft room for any connected league (Sleeper, Yahoo, ESPN). Features: commissioner scheduling, pre-draft lobby, Bloomberg Terminal dense layout, pick clock with auto-draft, real-time pick propagation via Socket.IO, per-user ranked best available with personal queue, chat, emoji reactions, and a post-draft recap with grades and export. This phase does NOT include auction drafts (Phase 5), video/audio (Phase 6), or dynasty rookie drafts (V2).

</domain>

<decisions>
## Implementation Decisions

### D-01: Panel Layout (Bloomberg Terminal)

**4-column fixed grid — LOCKED.**

Column assignment (left to right):
- **Left sidebar** (narrow): Queue panel (personal pick queue, drag-to-reorder) + Alerts panel below it (stacked)
- **Center-left** (widest): Draft Board — the pick history grid, always visible
- **Center-right**: Best Available — ranked player list with position tabs and search
- **Right sidebar** (narrow): My Roster + Chat stacked

Fixed proportions — no drag-resizing. All 4 columns always visible on desktop (≥1024px). Mobile tab strip per DR-01 scope: BOARD | PICKS | QUEUE | CHAT (Phase 8 handles mobile collapses).

Each panel has a **thin header bar**: panel label in JetBrains Mono ALL-CAPS (DRAFT BOARD, BEST AVAILABLE, MY ROSTER, QUEUE, CHAT, ALERTS) + chevron collapse toggle. Collapsed panel shows label bar only.

### D-02: Draft Board Grid

Fixed-size cells, horizontal scroll for leagues with more teams than viewport width allows.

**Pick cell content:**
- Player last name (14px semibold, `font-sans`)
- Position badge pill — color-coded: QB=`bg-red-700`, RB=`bg-green-700`, WR=`bg-blue-700`, TE=`bg-orange-700`, K=`bg-gray-600`, DEF=`bg-purple-700`
- NFL team abbreviation (12px, `text-muted`)
- Auto-pick: small robot icon badge (bottom-right of cell)
- Click cell: details drawer (who picked, when, alternates considered)

**"On the clock" indicator:**
- Active team's board column: pulsing `border-accent` glow animation
- Board header bar (above grid): `"TEAM NAME on the clock"` + countdown timer, large, always visible
- Empty pick cell in their column: blinking cursor

### D-03: Pick Clock

**Server-authoritative via Redis deadline timestamp.**

- On each pick (or draft start): server writes `draft:{id}:pick_deadline = now() + clock_seconds` to Redis
- Server broadcasts `pick_started` event with `deadline` epoch timestamp via Socket.IO
- Clients run local countdown from the deadline (no drift)
- Server fires `auto_draft` when Redis key TTL expires (server-side timer task via arq)
- Reconnecting clients: replay from `last_event_id` (see D-09), recalculate remaining time from stored deadline

**Warning states:**
- At 30s remaining: clock text → `text-warning` (amber `#F2B66D`)
- At 10s remaining: clock text → `text-danger` (red `#F26D6D`) + subtle pulse animation
- No audio at warning states

### D-04: Auto-Draft Behavior (DR-08)

When the pick clock expires, auto-draft fires:
1. If **personal queue is non-empty**: take the highest-ranked queued player still available
2. If **queue is empty**: take best available by **ADP + positional need weighting**
   - Score = FantasyCalc_rank_score + positional_need_bonus
   - `positional_need_bonus`: for each starter slot not yet filled, +N weight to that position
   - This prevents taking a 6th WR when QB slot is empty
3. Auto-picked cell shows robot icon badge in the board grid

### D-05: Commissioner Pause/Resume (DR-09)

- Commissioner controls visible only to the commissioner (role check via Socket.IO room auth)
- **Pause**: server stops the clock (deadline extended), broadcasts `draft_paused` event. All clients render semi-transparent overlay: `"DRAFT PAUSED"` centered. Board and chat remain visible behind overlay but board is non-interactive.
- **Resume**: commissioner clicks Resume. Server broadcasts `draft_resuming` with `countdown=5`. Clients show 5-second countdown overlay `"Resuming in 5..."`. Clock restarts with remaining time after countdown.

### D-06: Audio Cues (DR-07)

Two pre-bundled audio files (no external CDN):
1. **Pick sound** (`pick.mp3`): soft chime/click plays for all participants on each confirmed pick
2. **On-the-clock sound** (`your-turn.mp3`): distinct louder tone plays only for the picker whose turn it is

Both configurable via mute toggle in the draft room header (persisted per user in localStorage). Mute state does not affect other participants.

### D-07: Reconnect / Event Replay (DR-15)

- Socket.IO client tracks `lastEventId` (from each received event's metadata)
- On reconnect: client sends `{last_event_id}` with the `reconnect` event
- Server replays all draft events since that ID from the Redis stream (`XRANGE draft:{id}:events {last_event_id} +`)
- Client board rebuilds from replayed events — no separate REST snapshot needed
- Redis stream retention: minimum 48 hours per draft (arq cleanup task post-recap)

### D-08: Rankings Source

**FantasyCalc rankings** as the initial default (already integrated via `ProjectionService` in Phase 2).

- `overallRank` and `positionRank` from `GET /values/current` response power the best available sort
- Each participant can import custom rankings (DR-03): CSV or rank order from host platform
- Per-user overrides stored in DB (`UserDraftRanking` table, new in Phase 4)
- Rankings are **personal per user** — each participant has their own best available sort order
- The draft board (pick history grid) is shared and identical for all participants

### D-09: Queue UX

- **Add to queue**: star/heart icon button on hover in the best available list. Click = queue. Click again = remove.
- **Queue panel**: shows queued players in added order. Drag-and-drop to reorder.
- **Queue count**: shown in Queue panel header badge
- **On the clock**: best available list shows "FROM YOUR QUEUE" section at top (top 3 queued players still available) before the full ranked list continues below. Clear divider between the two sections.

### D-10: Best Available Filtering (DR-05/DR-13)

- **Position tab strip**: ALL | QB | RB | WR | TE | K | DEF — above the best available list
- **Live search box**: player name search, debounced 150ms
- Tabs and search can combine (e.g., filter to WR + search "Adams")
- Already-drafted players: **dim in place** (opacity-40, strikethrough), not removed — maintains tier context (DR-13)

### D-11: Tiered Cheat Sheet (DR-04)

Visual tier dividers embedded in the best available list:
- Horizontal divider rows: `"── TIER 1 (1–3) ──"` in JetBrains Mono, `text-muted`
- Tier boundaries auto-calculated from ADP gaps (configurable threshold, e.g., >15 rank delta between consecutive players = new tier)
- Visible in the same best available panel — no separate cheat sheet page
- Position tab filter applies: viewing QB tab shows only QB tiers

### D-12: Pre-Draft Flow

**Step 1 — Commissioner creates draft** (from My Connections / league detail page):
- "Schedule Draft" button appears for commissioner on any connected league card
- Draft setup page: pick clock (minutes per pick, default 90s), draft order method, date + time + timezone, optional roster preview window (how many rounds to show)
- On save: creates `Draft` DB record, sends ICS invite via `fastapi-mail` + in-app notification to all league members

**Step 2 — Pre-draft lobby** (`/draft` for participants, before draft starts):
- Shows: draft name, scheduled date/time, pick clock setting, participant list with online/offline presence (Socket.IO `/draft` namespace)
- Participants can: view their queue, import custom rankings, star players
- Commissioner additional controls: "Start Draft Early" button, "Randomize Order" button, drag-and-drop draft order panel
- Countdown to scheduled start time always visible

**Step 3 — Draft order setup (DR-02)**:
- Three modes in the commissioner's lobby panel:
  1. **Randomize** — shuffles list with animation, commission can re-randomize
  2. **Manual drag-and-drop** — drag team rows to set order
  3. **Import from host** — fetches existing draft order from Sleeper/Yahoo/ESPN API
- Order is locked automatically when draft starts (or commissioner clicks "Lock & Start")

### D-13: Post-Draft Recap (DR-14)

After the last pick, the draft room transitions to recap mode (same URL, same `/draft` route):
- **Team grades**: letter grade A–F per team, based on ADP value over expected (sum of ADP rank delta across all picks)
- **Value picks**: players taken >2 rounds later than their ADP
- **Reaches**: players taken >2 rounds earlier than their ADP  
- **Full pick log**: scrollable, all picks in order
- **Export options**: screenshot button (captures recap section as PNG image) + CSV pick log download
- PDF export deferred to Phase 8

### Claude's Discretion

- Emoji reaction set for picks (DR-11): fire, laugh, skeptical, applause — implementation of reaction storage and display (badge on pick cell) is Claude's to design
- Chat panel exact message format (timestamp, name, message, reactions)
- Pick details drawer exact layout (click on a pick cell)
- Alert panel content (who is on the clock, auto-pick notification, pause notification)
- Redis key naming conventions for draft events
- `Draft`, `DraftPick`, `DraftQueue`, `DraftChatMessage`, `UserDraftRanking` model schemas
- Pick sound + your-turn sound file selection (must be royalty-free, ≤100KB each)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/ROADMAP.md` — Phase 4 section, DR-01 through DR-15 requirements and success criteria
- `.planning/REQUIREMENTS.md` — DR-01 through DR-15 detailed acceptance criteria

### Architecture Decisions (locked)
- `.planning/PROJECT.md` — DECISION-003 (Bloomberg Terminal, LOCKED), Socket.IO + Redis namespaces `/league` and `/draft`, draft lock via Redis key, PostgreSQL rationale, hard August 2026 deadline
- `.planning/STATE.md` — Current project state, locked decisions accumulated

### Design System
- `.planning/phases/01-league-connector-mvp/01-UI-SPEC.md` — Design tokens (color palette, typography scale, component patterns), Radix UI + Tailwind setup. Color tokens: `bg-bg (#0B0E14)`, `bg-surface (#141822)`, `text-accent (#3DA9FC)`, `text-warning (#F2B66D)`, `text-danger (#F26D6D)`, `text-muted (#9AA3B2)`

### Existing Code (integration points)
- `backend/app/main.py` — Socket.IO already scaffolded (`socketio.AsyncServer`, `AsyncRedisManager`, mounted at `/ws`). Phase 4 adds `/draft` namespace events.
- `backend/app/services/projection_service.py` — FantasyCalc rankings (`overallRank`, `positionRank`) already fetched here; reuse for initial rankings in best available
- `frontend/src/components/Layout.tsx` — `/draft` route already hides bottom nav bar (`isDraft` flag); draft room gets full screen
- `frontend/src/components/ui/ChatBubble.tsx` — Reuse for draft chat messages
- `frontend/src/store/auth.ts` — Auth store pattern for Zustand; draft store should follow same pattern
- `frontend/src/lib/api.ts` — Axios instance with refresh interceptor; Socket.IO client is separate (not via Axios)

### Prior Phase Context
- `.planning/phases/02-team-manager-core/02-CONTEXT.md` — FantasyCalc endpoint verified: `GET /values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1`. Use `overallRank` + `positionRank`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `socketio.AsyncServer` + `AsyncRedisManager`: already mounted at `/ws` in `main.py`. Add `/draft` namespace events — no new server setup needed.
- `ChatBubble` + `TypingIndicator` components: available for draft chat panel reuse
- `ProgressBar` component: available for pick clock visualization
- `Toast` component: available for auto-draft notifications, pick announcements
- `FantasyCalc rankings` via `ProjectionService`: already fetched and cached; reuse as default rankings source
- `LeagueSwitcher` Zustand pattern: model `useDraftStore` on same pattern

### Established Patterns
- **Zustand stores** with localStorage persistence: `auth.ts` and `league.ts` are the patterns — `useDraftStore` should follow
- **arq background tasks**: `workers/tasks.py` pattern for auto-draft timer task and post-draft recap computation
- **Redis cache keys**: `CacheKey` class pattern in `cache.py` — add `CacheKey.draft_deadline(draft_id)`, `CacheKey.draft_state(draft_id)`, etc.
- **Radix UI + Tailwind**: all UI primitives composed this way; no new component libraries needed
- **Socket.IO connect/disconnect**: stubs exist in `main.py`; add `@sio.on('pick', namespace='/draft')` etc.

### Integration Points
- `/draft` route exists in `App.tsx` → `DraftPage.tsx` (file listed as untracked in git status — likely a stub)
- `Layout.tsx` already conditionally hides bottom nav on `/draft` — full-screen mode pre-wired
- `backend/app/api/v1/__init__.py` — add `draft.router` here
- New Alembic migration needed: `Draft`, `DraftPick`, `DraftQueue`, `DraftChatMessage`, `UserDraftRanking` models

</code_context>

<specifics>
## Specific Ideas

- **Bloomberg Terminal feel**: JetBrains Mono for ALL panel header labels. The panel header text style is `text-xs font-mono font-semibold tracking-widest text-muted`. This matches the terminal aesthetic without overloading the body copy.
- **Custom football/helmet SVGs**: Phase 1 UI-SPEC explicitly deferred custom football/helmet SVGs to Phase 4. Consider using for the pick clock center icon or the draft room header logo treatment.
- **Position color-coding** is a clear preference — make it consistent everywhere in the room: pick cells, best available rows, my roster panel, and queue items all use the same position badge color system.
- **August 2026 hard deadline**: The plan must be scoped to ship before August 2026 draft season. This means Phase 4 should be executable within ~6–8 weeks from planning.

</specifics>

<deferred>
## Deferred Ideas

- **PDF export of recap**: Deferred to Phase 8 (screenshot/PNG export covers Phase 4)
- **Mobile draft room layout**: Phase 8 — single-column collapse, bottom tab strip BOARD|QUEUE|CHAT (POL-01)
- **Video/audio overlay**: Phase 6 (Daily.co)
- **Auction draft variant**: Phase 5
- **Observer/spectator mode** (non-roster viewers): not discussed — V2 consideration
- **Commissioner pick-for-someone** (manual override of another team's pick): not discussed — Claude's discretion whether to include or defer
- **Pick clock configurable per round** (e.g., faster in later rounds): not discussed — likely Claude's discretion; single clock setting per draft is sufficient for Phase 4
- **ICS invite content details**: not discussed — Claude's discretion on format

</deferred>

---

*Phase: 04-live-draft-room*
*Context gathered: 2026-06-30*
