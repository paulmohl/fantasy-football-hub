# Phase 4: Live Draft Room (Snake) - Research

**Researched:** 2026-07-01
**Domain:** Real-time WebSocket draft room — Redis Streams, Socket.IO namespaces, arq timers, snake draft logic, Bloomberg Terminal grid
**Confidence:** HIGH (most claims verified against installed packages and official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Layout):** 4-column fixed grid — Left sidebar (Queue + Alerts), Center-left (Draft Board, widest), Center-right (Best Available), Right sidebar (My Roster + Chat). Fixed proportions, no drag-resize. Desktop ≥1024px always shows all 4 columns. Panel headers: JetBrains Mono ALL-CAPS + chevron collapse toggle.
- **D-02 (Draft Board):** Fixed-size cells, horizontal scroll. Pick cell: last name 14px semibold + position pill (QB=red-700, RB=green-700, WR=blue-700, TE=orange-700, K=gray-600, DEF=purple-700) + NFL team abbr + auto-pick robot badge. "On the clock" column: pulsing border-accent glow + board header bar with countdown.
- **D-03 (Pick Clock):** Server-authoritative via Redis deadline timestamp. Server writes `draft:{id}:pick_deadline = now() + clock_seconds`. Broadcast `pick_started` with epoch deadline. Clients countdown from deadline (no drift). arq fires auto_draft. Reconnecting clients replay from Redis stream and recalculate remaining time. Warning: 30s = text-warning, 10s = text-danger + pulse. No audio at warnings.
- **D-04 (Auto-Draft):** Queue non-empty → top queued available player; queue empty → best available by ADP + positional need weighting. Auto-pick flagged with robot badge.
- **D-05 (Commissioner Pause/Resume):** Commissioner controls via Socket.IO room auth. Pause → `draft_paused` event, semi-transparent overlay. Resume → `draft_resuming` with countdown=5, 5-second overlay, then clock restarts with remaining time.
- **D-06 (Audio):** Two pre-bundled files: `pick.mp3` (all participants, per pick), `your-turn.mp3` (active picker only). Configurable mute in header, persisted in localStorage. No external CDN.
- **D-07 (Reconnect):** Client tracks `lastEventId`. On reconnect: send `last_event_id`, server replays `XRANGE draft:{id}:events {last_event_id} +`. Client rebuilds board from replayed events — no REST snapshot needed. Stream retention: 48h minimum.
- **D-08 (Rankings):** FantasyCalc `overallRank`/`positionRank` as default (already in ProjectionService). Per-user CSV import → `UserDraftRanking` table. Each participant has their own best available sort order.
- **D-09 (Queue UX):** Add via star/heart hover button. Queue panel: added order, drag-to-reorder. Queue count badge. On the clock: "FROM YOUR QUEUE" section at top of best available (top 3 queued still available), clear divider.
- **D-10 (Best Available):** Position tab strip ALL|QB|RB|WR|TE|K|DEF + live search debounced 150ms. Tabs + search combine. Drafted players dim in place (opacity-40, strikethrough), not removed.
- **D-11 (Tiered Cheat Sheet):** Horizontal divider rows "── TIER 1 (1–3) ──" in JetBrains Mono text-muted. Auto-calculated from ADP gaps (threshold: >15 rank delta = new tier). Embedded in best available panel. Position tab filter applies.
- **D-12 (Pre-Draft Flow):** Step 1 — commissioner "Schedule Draft" button on league card → setup page (pick clock, draft order method, date/time/timezone, roster preview). ICS invite + in-app notification on save. Step 2 — lobby at `/draft` for all participants (presence, queue, rankings import, commissioner controls). Step 3 — draft order: Randomize / Manual drag / Import from host platform.
- **D-13 (Post-Draft Recap):** Same URL, same `/draft` route after last pick. Team grades A–F from ADP value over expected. Value picks (>2 rounds after ADP), reaches (>2 rounds before ADP), full pick log. Screenshot → PNG export. CSV pick log download. PDF deferred to Phase 8.

### Claude's Discretion

- Emoji reaction set (fire, laugh, skeptical, applause): storage pattern and display design
- Chat panel exact message format (timestamp, name, message, reactions)
- Pick details drawer exact layout
- Alert panel content
- Redis key naming conventions for draft events
- `Draft`, `DraftPick`, `DraftQueue`, `DraftChatMessage`, `UserDraftRanking` model schemas
- Pick sound + your-turn sound file selection (royalty-free, ≤100KB each)

### Deferred Ideas (OUT OF SCOPE)

- PDF export of recap — Phase 8
- Mobile draft room layout (single-column collapse, bottom tab strip) — Phase 8
- Video/audio overlay — Phase 6 (Daily.co)
- Auction draft variant — Phase 5
- Observer/spectator mode — V2
- Commissioner pick-for-someone — not discussed (defer or Claude's discretion)
- Pick clock configurable per round — single clock per draft is sufficient for Phase 4
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DR-01 | Commissioner schedules draft (date, time, timezone, pick clock, roster preview); all members receive ICS + in-app notification | icalendar 7.2.0 + fastapi-mail pattern documented |
| DR-02 | Commissioner can randomize, manually order, or import draft order; locked on start | @dnd-kit/sortable already in package.json |
| DR-03 | User imports custom rankings (CSV or host platform); drag-and-drop multi-select edit panel | UserDraftRanking model + CSV parse → fuzzy match via PlayerCrossMap |
| DR-04 | Tiered cheat sheet per position; star players to queue | ADP gap threshold algorithm documented |
| DR-05 | Bloomberg Terminal 4-column layout (DECISION-003); all panels simultaneously visible; on-the-clock always visible | CSS Grid pattern verified |
| DR-06 | On-the-clock stage: team name, large countdown, queue, auto-pick suggestions; desktop/push notifications | Redis deadline + Socket.IO emit pattern |
| DR-07 | Pick propagates to all participants within 500ms; audio cue; next picker announced | Socket.IO room broadcast; 500ms verifiable via Playwright timing |
| DR-08 | Timeout: highest-ranked queued player auto-drafted; if empty, best ADP available; flagged as auto-pick | arq deferred task + idempotent check pattern |
| DR-09 | Commissioner pause (clock stops, overlay) + resume (5-second countdown) | Socket.IO commissioner-only emit pattern |
| DR-10 | Chat messages visible within 200ms; scrolls without stealing board focus; pre-draft history preserved | Socket.IO chat event; DB persistence |
| DR-11 | Pick emoji reactions (fire, laugh, skeptical, applause); badges on pick cards | JSONB reactions column on draft_picks |
| DR-12 | Draft board updates in real time; clicking pick shows details (when, who, alternates) | Socket.IO room broadcast + details drawer |
| DR-13 | Position filter highlights matching picks, dims others | CSS opacity-40 + position filter state |
| DR-14 | Post-draft recap: team grades, value picks, reaches, position-need scores, full pick log; PNG and CSV export | html2canvas + ADP delta algorithm |
| DR-15 | Socket.IO + Redis adapter + draft lock; clients track last event ID; replay missed events from Redis stream | XADD/XRANGE + arq + Redis SETNX lock pattern |
</phase_requirements>

---

## Summary

Phase 4 is a real-time multi-user application with five distinct subsystems: the WebSocket event bus, the draft state machine, the pick clock timer, the Bloomberg Terminal UI, and the post-draft analytics layer. All five have strong infrastructure already in place — `python-socketio` 5.16.3, `redis` 8.0.1 with Stream support, `arq` with deferred jobs, `@dnd-kit/sortable` for drag ordering, and `socket.io-client` 4.7.5+ in the frontend.

Two packages are missing and must be added in Wave 0: `icalendar>=7.2.0` (Python, for ICS calendar invites) and `html2canvas@^1.4.0` (npm, for PNG recap export). Everything else is already installed.

The critical architectural insight is that the draft room is event-sourced via Redis Streams. The board state for every client — including reconnecting clients — is derived entirely from replaying the stream, not from a REST snapshot. This means correct XADD field design and XRANGE replay are load-bearing decisions. The pick clock uses server-authoritative Redis timestamps; clients never trust their local wall clock for the deadline.

**Primary recommendation:** Build the `/draft` Socket.IO namespace as a class-based `AsyncNamespace`, use Redis Streams (`XADD`/`XRANGE`) for event sourcing, and implement the auto-draft timer as an arq deferred task with a unique `_job_id` per pick and an idempotent guard inside the task body.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pick submission and validation | API / Backend | — | Server is authoritative; clients never trust client-submitted picks without server re-validation |
| Pick clock deadline | API / Backend (Redis) | Browser (display only) | Server writes epoch timestamp; clients calculate remaining from it — never from a local start time |
| Auto-draft timer | Background Worker (arq) | — | arq deferred job is the only process with a guaranteed execution context after N seconds |
| Event propagation to participants | API / Backend (Socket.IO) | — | Server emits to room after confirmed DB write |
| Draft board state reconstruction | Browser / Client | — | Client rebuilds from replayed Stream events; no server-rendered board |
| Draft order setup (drag-and-drop) | Browser / Client | API / Backend (persist) | Interaction is client-side; final order persisted to DB before draft start |
| Queue management | Browser / Client | API / Backend (persist) | Client manages queue UI; server persists and serves for reconnect |
| Best available ranking | API / Backend | Browser / Client (filter/search) | FantasyCalc + user override merge is server-computed; filtering/search is client-side |
| ICS invite generation | API / Backend | — | Server generates and sends via fastapi-mail |
| Post-draft grade computation | API / Backend | — | ADP data needed for grading is server-side |
| PNG export | Browser / Client | — | html2canvas captures DOM; no server-side rendering needed |
| Commissioner controls | API / Backend (auth check) | Browser (UI gate) | Role verified on server in Socket.IO `on_connect` and per-event; UI gate is UX only |

---

## Standard Stack

### Core (already installed — no new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python-socketio` | 5.16.3 [VERIFIED: pip] | `/draft` namespace, room fan-out | Already mounted at `/ws` in `main.py`; `AsyncRedisManager` already set up |
| `redis` (redis.asyncio) | 8.0.1 [VERIFIED: pip] | Redis Streams (XADD/XRANGE), draft deadline key, available-players SET, draft lock | Native async API; already used throughout codebase |
| `arq` | installed (see workers/tasks.py) [VERIFIED: codebase] | Auto-draft timer deferred task; post-draft recap arq task | Already used for prewarm and credential check tasks |
| `fastapi-mail` | 1.6.5 [VERIFIED: pip] | Sending ICS invite emails | Already in pyproject.toml |
| `socket.io-client` | ^4.7.5 (4.8.3 latest) [VERIFIED: package.json] | Frontend Socket.IO namespace connect, reconnect | Already in package.json; namespace connect with auth dict |
| `@dnd-kit/core` | ^6.3.1 [VERIFIED: package.json] | Drag-and-drop for draft order setup and queue reorder | Already installed; used in Phase 2 lineup drag |
| `@dnd-kit/sortable` | ^10.0.0 [VERIFIED: package.json] | `useSortable` hook for vertical list reordering | Already installed |

### New Packages Required (Wave 0 additions)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `icalendar` | >=7.2.0 [VERIFIED: pip index, currently 7.2.0] | ICS calendar invite generation (DR-01) | RFC 5545 compliant; `Calendar.new()` + `Event.new()` + `add_missing_timezones()` API; Python stdlib `zoneinfo` for timezone handling |
| `html2canvas` | ^1.4.0 [VERIFIED: npm view, 1.4.1 available] | Client-side PNG export of recap section (DR-14) | Browser-native canvas rendering; no server process needed; `toBlob()` API for efficient export |

**Installation:**
```bash
# Backend
pip install "icalendar>=7.2.0"
# Add to pyproject.toml [project] dependencies

# Frontend
npm install html2canvas@^1.4.0
```

**Version verification:**
```bash
pip index versions icalendar   # => 7.2.0 current
npm view html2canvas version   # => 1.4.1 current
```

### Already Available (no install needed)

| Library | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/react-dialog` | in package.json | Pick details drawer, pause overlay modal |
| `@radix-ui/react-tooltip` | in package.json | Player hover info in best available list |
| `zustand` | ^4.5.2 | `useDraftStore` — follow `auth.ts` persist pattern |
| `@tanstack/react-query` | ^5.45.0 | Draft setup REST endpoints |
| `recharts` | ^3.9.0 | Post-draft recap charts (if any) |

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (Participant)          Backend Server              Background (arq worker)
─────────────────────          ──────────────              ───────────────────────
DraftPage.tsx                  Socket.IO /draft             auto_draft_pick task
  useDraftStore (Zustand)  ←── AsyncNamespace          ←── arq deferred job
  socket.io-client         ──→ on_connect(auth)        ──→ [fires at deadline]
    connect({auth:{token,       verify JWT                    check current_pick_num
             draft_id}})        enter_room(draft:{id})        if stale → exit
                                                              else → pick best player
  emit("pick", {player_id})  ──→ on_pick()                   emit pick_confirmed
                                  SETNX draft:{id}:lock
  on("pick_confirmed")       ←──  validate player available   post_draft_recap task
  on("pick_started")         ←──  DB insert DraftPick         [enqueued after last pick]
  on("auto_drafted")         ←──  SREM from available SET     compute ADP grades
  on("draft_paused")         ←──  XADD draft:{id}:events      save to DB
  on("draft_resuming")       ←──  emit to room
  on("reaction_added")       ←──  update JSONB reactions
  on("chat_message")         ←──  DB insert ChatMessage

  [on reconnect]
  emit("reconnect",               on_reconnect()
       {last_event_id})       ──→ XRANGE draft:{id}:events
  [batch replay events]      ←──  since last_event_id

Redis                          PostgreSQL
─────                          ──────────
draft:{id}:events (Stream)     drafts
draft:{id}:pick_deadline       draft_picks (+ reactions JSONB)
draft:{id}:current_pick        draft_queue
draft:{id}:state               draft_chat_messages
draft:{id}:lock (SETNX 5s)     user_draft_rankings
draft:{id}:available (SET)
```

### Recommended Project Structure

```
backend/app/
├── models/
│   └── draft.py           # Draft, DraftPick, DraftQueue, DraftChatMessage, UserDraftRanking
├── api/v1/
│   └── draft.py           # REST routes: schedule, setup, recap, rankings import
├── sockets/
│   └── draft_namespace.py # AsyncNamespace('/draft') class-based handler
├── services/
│   └── draft_service.py   # pick validation, snake order, auto-draft selection, grade computation
└── workers/
    tasks.py               # add auto_draft_pick() and post_draft_recap() to functions list

frontend/src/
├── store/
│   └── draft.ts           # useDraftStore (Zustand + persist) — follow auth.ts pattern
├── lib/
│   └── socket.ts          # socket.io-client instance for /draft namespace + reconnect logic
├── pages/
│   └── DraftPage.tsx      # entry point; delegates to lobby or live draft room
└── components/draft/
    ├── DraftRoom.tsx       # 4-column grid layout shell
    ├── DraftBoard.tsx      # pick grid (NxM), horizontal scroll
    ├── BestAvailable.tsx   # ranked player list + tier dividers + position tabs + search
    ├── QueuePanel.tsx      # personal queue + drag-reorder (@dnd-kit/sortable)
    ├── RosterPanel.tsx     # my team picks so far
    ├── ChatPanel.tsx       # reuse ChatBubble + TypingIndicator
    ├── AlertsPanel.tsx     # on-the-clock, auto-pick, pause notifications
    ├── PickClock.tsx       # server-deadline countdown display
    ├── PickDrawer.tsx      # click-a-pick details drawer (Radix Dialog)
    ├── DraftRecap.tsx      # post-draft grades, value picks, reaches, export
    └── PreDraftLobby.tsx   # scheduled lobby + commissioner controls
```

### Pattern 1: Socket.IO Class-Based Namespace

**What:** `AsyncNamespace` subclass registered via `sio.register_namespace()` at module load time.
**When to use:** Always — for `/draft`. Class-based grouping keeps event handlers cohesive and provides session storage via `save_session`/`get_session`.

```python
# Source: https://github.com/miguelgrinberg/python-socketio
import socketio
from app.core.security import decode_access_token

class DraftNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid: str, environ: dict, auth: dict | None = None) -> None:
        if not auth or not auth.get("token"):
            raise socketio.exceptions.ConnectionRefusedError("auth_required")
        try:
            payload = decode_access_token(auth["token"])
        except Exception:
            raise socketio.exceptions.ConnectionRefusedError("invalid_token")
        draft_id = auth.get("draft_id")
        if not draft_id:
            raise socketio.exceptions.ConnectionRefusedError("draft_id_required")
        await self.save_session(sid, {"user_id": payload["sub"], "draft_id": draft_id})
        await self.enter_room(sid, f"draft:{draft_id}")

    async def on_disconnect(self, sid: str, reason: str) -> None:
        session = await self.get_session(sid)
        if session:
            await self.emit(
                "member_presence",
                {"user_id": session["user_id"], "online": False},
                room=f"draft:{session['draft_id']}",
                skip_sid=sid,
            )

    async def on_pick(self, sid: str, data: dict) -> dict:
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        # ... validate, record, XADD, emit to room
        await self.emit("pick_confirmed", pick_data, room=f"draft:{draft_id}")
        return {"ok": True}

    async def on_reconnect(self, sid: str, data: dict) -> None:
        session = await self.get_session(sid)
        last_event_id = data.get("last_event_id", "-")
        events = await redis.xrange(f"draft:{session['draft_id']}:events", min=last_event_id, max="+")
        for event_id, fields in events:
            if event_id == last_event_id:
                continue  # skip the boundary event itself
            await self.emit("replay_event", {"id": event_id, **fields}, to=sid)

# Register at module level (before ASGIApp is built)
sio.register_namespace(DraftNamespace("/draft"))
```

### Pattern 2: Redis Streams for Event Sourcing

**What:** `XADD` on every state-changing draft event; `XRANGE` for client reconnect replay.
**When to use:** Every pick, auto-pick, pause, resume, chat message, and draft state transition.

```python
# Source: https://redis.readthedocs.io/en/stable/
import time

async def record_draft_event(redis, draft_id: str, event_type: str, fields: dict) -> str:
    """Write a draft event to the Redis Stream and return the event ID."""
    stream_key = f"draft:{draft_id}:events"
    payload = {"type": event_type, "ts": str(time.time()), **fields}
    event_id = await redis.xadd(
        stream_key,
        payload,
        maxlen=5000,      # cap at 5000 events; ~30-team x 15-round drafts produce ~450 picks
        approximate=True, # allow slight overshoot for performance
    )
    return event_id  # returns b"1714000000000-0" style bytes

# Client reconnect replay (exclusive start: '(' prefix)
async def replay_since(redis, draft_id: str, last_event_id: str) -> list[tuple]:
    """Return all events after last_event_id (exclusive)."""
    events = await redis.xrange(
        f"draft:{draft_id}:events",
        min=f"({last_event_id}",  # '(' prefix = exclusive; avoid re-sending boundary event
        max="+",
    )
    return events  # list of (event_id_bytes, fields_dict)
```

### Pattern 3: arq Auto-Draft Timer (Idempotent Guard)

**What:** Enqueue a deferred arq job per pick with a unique `_job_id`. Job checks current pick number before acting.
**When to use:** After every confirmed pick to arm the timer for the next pick.

```python
# Source: https://arq-docs.helpmanual.io/
from datetime import datetime, UTC
from arq import create_pool
from arq.connections import RedisSettings

async def auto_draft_pick(ctx: dict, draft_id: str, pick_num: int) -> None:
    """Auto-draft the current pick if it hasn't been made yet.
    
    Idempotent: if current_pick_num in Redis != pick_num, another pick was made — exit silently.
    """
    redis = ctx["redis"]
    current = await redis.get(f"draft:{draft_id}:current_pick")
    if current is None or int(current) != pick_num:
        return  # pick already made; nothing to do
    
    # Execute auto-pick: queue first, then ADP+need
    best_player_id = await _select_auto_draft_player(redis, draft_id)
    if not best_player_id:
        return  # draft complete or no available players
    
    await _execute_pick(redis, draft_id, pick_num, best_player_id, is_auto=True)

async def arm_auto_draft_timer(redis_pool, draft_id: str, pick_num: int, deadline_epoch: float) -> None:
    """Enqueue auto-draft job for pick_num to fire at deadline."""
    deadline_dt = datetime.fromtimestamp(deadline_epoch, tz=UTC)
    await redis_pool.enqueue_job(
        "auto_draft_pick",
        draft_id=str(draft_id),
        pick_num=pick_num,
        _defer_until=deadline_dt,
        _job_id=f"autodraft:{draft_id}:{pick_num}",  # unique per pick; no collision
        _expires=deadline_dt,  # if somehow missed, don't run stale auto-picks
    )

class WorkerSettings:
    functions = [..., auto_draft_pick, post_draft_recap]
    allow_abort_jobs = True  # enables job.abort() if needed for edge cases
```

### Pattern 4: Pick Clock — Server Authority

**What:** Server writes epoch timestamp to Redis; client subtracts `Date.now()` to get remaining ms.
**When to use:** Every `pick_started` event.

```python
# Backend: set deadline on each pick_started
import time
async def start_pick_clock(redis, draft_id: str, clock_seconds: int) -> float:
    deadline = time.time() + clock_seconds
    await redis.set(f"draft:{draft_id}:pick_deadline", str(deadline), ex=clock_seconds + 30)
    return deadline
```

```typescript
// Frontend: derive remaining from server deadline, never from a local start time
// Source: [ASSUMED] standard approach for server-clock synchronization
interface PickStartedEvent {
  deadline: number  // epoch seconds (float)
  pick_num: number
  team_id: string
}

function usePickClock(deadline: number | null) {
  const [remaining, setRemaining] = useState<number>(0)

  useEffect(() => {
    if (!deadline) return
    const interval = setInterval(() => {
      const ms = Math.max(0, deadline * 1000 - Date.now())
      setRemaining(Math.floor(ms / 1000))
    }, 250)  // 250ms tick — smooth countdown without excessive renders
    return () => clearInterval(interval)
  }, [deadline])

  return remaining
}
```

### Pattern 5: Draft Lock (One Writer Per Pick)

**What:** `SETNX` Redis key with 5-second TTL prevents two simultaneous picks on the same slot.
**When to use:** At the beginning of every `on_pick` handler.

```python
# Source: redis.asyncio SETNX pattern [VERIFIED: redis-py docs]
async def acquire_pick_lock(redis, draft_id: str, sid: str, ttl: int = 5) -> bool:
    """Return True if lock acquired, False if another pick is in flight."""
    lock_key = f"draft:{draft_id}:pick_lock"
    result = await redis.set(lock_key, sid, nx=True, ex=ttl)
    return result is not None  # SET NX returns None if key exists

async def release_pick_lock(redis, draft_id: str) -> None:
    await redis.delete(f"draft:{draft_id}:pick_lock")
```

### Pattern 6: ICS Calendar Invite

**What:** Generate an `.ics` file attachment and send via `fastapi-mail`.
**When to use:** When commissioner saves draft schedule (DR-01).

```python
# Source: https://github.com/collective/icalendar
from icalendar import Calendar, Event
from datetime import timedelta
from zoneinfo import ZoneInfo

def build_draft_ics(
    draft_name: str,
    scheduled_at: datetime,
    timezone_str: str,
    num_teams: int,
    clock_seconds: int,
    num_rounds: int = 15,
) -> bytes:
    tz = ZoneInfo(timezone_str)
    start = scheduled_at.replace(tzinfo=tz) if scheduled_at.tzinfo is None else scheduled_at
    # Rough estimate: all picks + pauses. Minimum 2 hours.
    estimated_seconds = num_teams * num_rounds * clock_seconds
    duration = timedelta(seconds=max(7200, estimated_seconds))

    event = Event.new(
        summary=f"Fantasy Draft: {draft_name}",
        start=start,
        end=start + duration,
        location="Fantasy Football Hub",
        description="Draft room opens 15 minutes before scheduled start.",
    )
    cal = Calendar.new(subcomponents=[event])
    cal.add_missing_timezones()  # adds VTIMEZONE component for client compatibility
    return cal.to_ical()
```

### Pattern 7: PNG Recap Export

**What:** `html2canvas` captures the DOM recap section as a canvas, then triggers a download.
**When to use:** When user clicks the "Export as Image" button in `DraftRecap.tsx`.

```typescript
// Source: https://github.com/niklasvh/html2canvas
import html2canvas from 'html2canvas'

async function exportRecapAsPNG(draftId: string): Promise<void> {
  const element = document.getElementById('draft-recap')
  if (!element) return
  const canvas = await html2canvas(element, {
    scale: 2,          // 2x resolution for crisp export
    useCORS: true,     // allow cross-origin images if any
    backgroundColor: '#0B0E14',  // match bg-bg token to avoid white flash
  })
  canvas.toBlob((blob) => {
    if (!blob) return
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.download = `draft-recap-${draftId}.png`
    link.href = url
    link.click()
    URL.revokeObjectURL(url)
  }, 'image/png')
}
```

### Pattern 8: Bloomberg Terminal CSS Grid Layout

**What:** 4-column fixed grid using Tailwind's arbitrary value syntax.
**When to use:** `DraftRoom.tsx` outer shell.

```tsx
// Source: CSS Grid spec [ASSUMED: standard Tailwind arbitrary value usage]
// All 4 columns always visible on desktop (≥1024px per D-01)
export function DraftRoom() {
  return (
    <div className="grid grid-cols-[200px_1fr_320px_200px] h-screen overflow-hidden bg-bg">
      {/* Left sidebar: Queue + Alerts stacked */}
      <div className="flex flex-col overflow-hidden border-r border-border">
        <QueuePanel />
        <AlertsPanel />
      </div>

      {/* Center-left: Draft Board (widest) */}
      <div className="flex flex-col overflow-hidden border-r border-border">
        <BoardHeader />  {/* "TEAM NAME on the clock" + countdown */}
        <div className="overflow-x-auto flex-1">  {/* horizontal scroll for wide leagues */}
          <DraftBoard />
        </div>
      </div>

      {/* Center-right: Best Available */}
      <div className="flex flex-col overflow-hidden border-r border-border">
        <BestAvailable />
      </div>

      {/* Right sidebar: My Roster + Chat stacked */}
      <div className="flex flex-col overflow-hidden">
        <RosterPanel />
        <ChatPanel />
      </div>
    </div>
  )
}
```

Draft board inner grid (NxM picks):
```tsx
// N = num_teams + 1 (rank column). M = num_rounds rows.
// Horizontal scroll is on the parent container.
<div
  className="grid"
  style={{ gridTemplateColumns: `repeat(${numTeams + 1}, 80px)` }}
>
  {picks.map(pick => <PickCell key={pick.pick_num} pick={pick} />)}
</div>
```

### Pattern 9: Zustand Draft Store

**What:** `useDraftStore` following the `auth.ts` + `league.ts` persist pattern.
**When to use:** Single source of truth for all client-side draft state.

```typescript
// Source: codebase — frontend/src/store/auth.ts pattern [VERIFIED: codebase]
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface DraftState {
  draftId: string | null
  status: 'idle' | 'lobby' | 'live' | 'paused' | 'complete'
  currentPickNum: number
  currentTeamId: string | null
  deadline: number | null          // epoch seconds from server
  lastEventId: string | null       // for reconnect replay
  queue: string[]                  // player_ids in queue order
  picks: DraftPickEvent[]          // board state rebuilt from events
  muteAudio: boolean
  setDraft: (draftId: string) => void
  applyEvent: (event: DraftEvent) => void
  setDeadline: (deadline: number) => void
  addToQueue: (playerId: string) => void
  removeFromQueue: (playerId: string) => void
  reorderQueue: (from: number, to: number) => void
  toggleMute: () => void
}

export const useDraftStore = create<DraftState>()(
  persist(
    (set) => ({
      // ... initial state + reducers
      muteAudio: false,
    }),
    {
      name: 'ffhub-draft',
      partialize: (s) => ({ muteAudio: s.muteAudio }),  // only persist mute preference
    },
  ),
)
```

### Pattern 10: Snake Draft Order

**What:** Pure function for computing next-picker slot.
**When to use:** `draft_service.py` — called on every confirmed pick.

```python
# Source: [ASSUMED] snake draft standard algorithm
def snake_pick_to_slot(pick_num: int, num_teams: int) -> tuple[int, int]:
    """Return (round, team_slot_0_indexed) for pick_num (1-indexed)."""
    round_num = (pick_num - 1) // num_teams + 1
    pos_in_round = (pick_num - 1) % num_teams
    if round_num % 2 == 1:  # odd rounds: left to right (slot 0..N-1)
        team_slot = pos_in_round
    else:                   # even rounds: right to left (slot N-1..0)
        team_slot = num_teams - 1 - pos_in_round
    return round_num, team_slot
```

### Pattern 11: ADP Grade Computation

**What:** Map ADP delta sum per team to letter grade A–F.
**When to use:** `post_draft_recap` arq task after final pick.

```python
# Source: [ASSUMED] standard ADP value scoring approach
def compute_adp_grades(
    picks_by_team: dict[str, list[dict]],  # team_id -> list of {pick_num, player_id}
    adp_lookup: dict[str, float],          # player_id -> ADP rank (FantasyCalc overallRank)
) -> dict[str, str]:
    """Compute letter grade for each team based on ADP value accumulated."""
    team_scores: dict[str, float] = {}
    for team_id, picks in picks_by_team.items():
        # Positive delta = picked better than ADP (steal); negative = overdrafted (reach)
        total = sum(
            adp_lookup.get(p["player_id"], p["pick_num"]) - p["pick_num"]
            for p in picks
        )
        team_scores[team_id] = total

    sorted_scores = sorted(team_scores.values(), reverse=True)
    n = len(sorted_scores)

    def to_grade(score: float) -> str:
        rank = sorted_scores.index(score)
        pct = rank / n
        if pct < 0.15:   return "A+"
        if pct < 0.30:   return "A"
        if pct < 0.45:   return "B"
        if pct < 0.60:   return "C"
        if pct < 0.80:   return "D"
        return "F"

    return {team_id: to_grade(score) for team_id, score in team_scores.items()}
```

### Anti-Patterns to Avoid

- **Client-authoritative pick clock:** Never derive the deadline from a client-side `Date.now() + clock_seconds`. The server is authoritative. Clients ONLY calculate remaining time from the server-provided deadline epoch.
- **Board state from REST on reconnect:** Do NOT add a `/api/v1/draft/{id}/state` REST snapshot endpoint as the primary reconnect path. Rebuild entirely from XRANGE replay. Snapshot is only for performance optimization if stream replay proves slow.
- **Consumer groups for event replay:** XREADGROUP is for competing consumers processing events once. Client replay uses plain XRANGE — multiple clients can replay the same events independently without consumer group coordination.
- **Emitting before DB write:** Never emit `pick_confirmed` to the room before the `DraftPick` row is committed. If the emit succeeds but the DB write fails, clients diverge from server state.
- **Registering namespace inside startup event:** `sio.register_namespace()` must be called at module level, before `socketio.ASGIApp(sio, ...)` is constructed. Calling it inside `@app.on_event("startup")` is too late.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ICS calendar file generation | Custom RFC 5545 string formatting | `icalendar>=7.2.0` | VTIMEZONE component, recurrence rules, property encoding, and RFC compliance are error-prone to hand-roll |
| Client-side PNG screenshot | Server-side puppeteer or wkhtmltoimage | `html2canvas@^1.4.0` | Client-side; no server process; works with live DOM state including animations that server renders can't capture |
| Drag-and-drop queue reorder | Native HTML5 drag events | `@dnd-kit/sortable` (already installed) | Accessibility, touch support, animation, and scroll-during-drag are all handled; native drag has cross-browser inconsistency |
| Pick clock countdown | `setTimeout` chains | `setInterval` with server deadline epoch | Server epoch makes the countdown immune to tab-switching, sleep, and clock drift; `setTimeout` chains accumulate error |
| Real-time event fan-out | Long-polling or SSE | Socket.IO + Redis adapter (already set up) | Multi-instance fan-out via Redis pub/sub; automatic reconnect; room management |
| Draft event log | PostgreSQL append-only table | Redis Streams (`XADD`) | Streams are ordered by ID, support `XRANGE` replay, and have built-in `maxlen` trimming; no scan needed for replay |

**Key insight:** The real-time and event sourcing primitives are already infrastructure-level in this project. Phase 4's job is to add events and consumers, not to build transport or persistence from scratch.

---

## Common Pitfalls

### Pitfall 1: Redis XRANGE Inclusive vs Exclusive Boundary

**What goes wrong:** Client sends `last_event_id` and server calls `xrange(key, min=last_event_id, max="+")`. The boundary event is included, so the client receives the last event it already processed as the first replayed event. Client applies the same pick twice.

**Why it happens:** `XRANGE` start is inclusive by default.

**How to avoid:** Use `min=f"({last_event_id}"` (parenthesis prefix = exclusive in Redis protocol).

```python
events = await redis.xrange(stream_key, min=f"({last_event_id}", max="+")
```

**Warning signs:** Duplicate picks appearing in the board after reconnect.

---

### Pitfall 2: Namespace Registration Timing

**What goes wrong:** `sio.register_namespace(DraftNamespace('/draft'))` called inside `@app.on_event("startup")`. The `socketio.ASGIApp(sio, ...)` wrapper is already built at module load time. Events sent to `/draft` are not dispatched to the namespace class.

**Why it happens:** `ASGIApp` captures the server state at construction time. Post-construction namespace registration may not be reflected in all dispatch paths.

**How to avoid:** Call `sio.register_namespace()` at module level in `main.py`, BEFORE `combined_app = socketio.ASGIApp(sio, ...)`.

**Warning signs:** `/draft` events fall through to the default namespace handlers (the bare `@sio.event` functions at the top of `main.py`).

---

### Pitfall 3: arq Job ID Collision on First Pick

**What goes wrong:** Using `_job_id=f"autodraft:{draft_id}"` (without pick number) means after the first pick is made and a new timer is enqueued for pick 2, arq returns `None` because a job with that ID still exists in the queue (if pick 1's timer is still deferred).

**Why it happens:** arq `_job_id` uniqueness check includes jobs that are deferred but not yet run.

**How to avoid:** Use `_job_id=f"autodraft:{draft_id}:{pick_num}"` — pick number makes every timer unique. The idempotent check inside the task handles stale timers.

**Warning signs:** `enqueue_job` returns `None`; auto-draft never fires for picks after the first.

---

### Pitfall 4: html2canvas Cross-Origin Images

**What goes wrong:** The recap section includes player images or external URLs. `html2canvas` fails silently on cross-origin resources (canvas is tainted), producing a blank or partial export.

**Why it happens:** Browser canvas CORS security — tainted canvas cannot be exported to `toBlob()`.

**How to avoid:** Serve player images through the backend proxy or use only same-origin resources in the recap. Set `useCORS: true` AND ensure the image server sends `Access-Control-Allow-Origin: *`.

**Warning signs:** Exported PNG is blank where images should appear; `canvas.toBlob()` throws `SecurityError: Failed to execute 'toBlob' on 'HTMLCanvasElement': Tainted canvases may not be exported`.

---

### Pitfall 5: icalendar VTIMEZONE Missing in Old Versions

**What goes wrong:** Using `icalendar<7.x`, the `add_missing_timezones()` method does not exist or does not auto-populate the VTIMEZONE component. Calendar clients (Google Calendar, Outlook) that depend on VTIMEZONE for DST handling misinterpret the event time.

**Why it happens:** `add_missing_timezones()` was added in icalendar 5.x but the exact API changed across versions.

**How to avoid:** Pin `icalendar>=7.2.0` in `pyproject.toml`. The `Calendar.new()` + `Event.new()` + `calendar.add_missing_timezones()` pattern is the current documented API.

**Warning signs:** ICS opens in Google Calendar with wrong timezone; Outlook shows event 5 hours off.

---

### Pitfall 6: Draft Board Horizontal Overflow in Center-Left Column

**What goes wrong:** The center-left column is `1fr` of the 4-column grid. If the draft board inner grid is wider than the available space, it causes the entire page layout to overflow (all 4 columns shrink or the page scrolls horizontally).

**Why it happens:** CSS Grid `1fr` columns can overflow their parent if a child has an explicit width greater than `1fr`.

**How to avoid:** Set `overflow-x: auto` on the **draft board container** (the direct child of the center-left column), NOT on the center-left column itself. The column must have `overflow: hidden` (or `min-width: 0` which prevents grid blowout).

```tsx
{/* Center-left column: min-w-0 prevents grid blowout */}
<div className="flex flex-col overflow-hidden min-w-0 border-r border-border">
  <BoardHeader />
  {/* overflow-x-auto on the INNER container, not the column */}
  <div className="overflow-x-auto flex-1">
    <DraftBoard />
  </div>
</div>
```

**Warning signs:** Adding a 20-team draft causes all 4 columns to collapse to minimum width.

---

### Pitfall 7: Socket.IO Auth Dict Is Separate from environ

**What goes wrong:** Code tries to read JWT from `environ` headers (e.g., `environ.get("HTTP_AUTHORIZATION")`). For Socket.IO namespace connections, the auth dict sent by the client is in the `auth` parameter of `on_connect`, not in `environ`.

**Why it happens:** Confusion between HTTP request headers (environ) and Socket.IO connection auth payload.

**How to avoid:** Client sends: `io('/draft', { auth: { token: accessToken, draft_id: draftId } })`. Server reads: `auth["token"]` in `on_connect(self, sid, environ, auth)`.

---

### Pitfall 8: Position Need Weighting for Auto-Draft

**What goes wrong:** Auto-draft by pure ADP selects 6 WRs for a team that already has 5 WRs and no QB, because WRs rank highest by ADP at that point.

**Why it happens:** ADP is league-average value, not personalized to a specific team's roster composition.

**How to avoid:** Implement positional need bonus as described in D-04:
```python
def positional_need_bonus(roster: list[str], position: str, roster_format: dict) -> float:
    """Return a bonus score that biases toward unfilled starting slots."""
    pos_count = sum(1 for p in roster if get_position(p) == position)
    starter_slots = roster_format.get(position, {}).get("slots", 0)
    unfilled = max(0, starter_slots - pos_count)
    return unfilled * 5.0  # 5 rank positions of bonus per unfilled slot
```

---

## Model Schemas (Claude's Discretion)

Recommended schemas for the 5 new SQLAlchemy models (Alembic migration `003_phase4_draft`):

```python
# backend/app/models/draft.py
from sqlalchemy.dialects.postgresql import JSONB

class Draft(Base):
    __tablename__ = "drafts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    commissioner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(default="pending")  # pending|live|paused|complete
    scheduled_at: Mapped[datetime | None] = mapped_column(default=None)
    timezone: Mapped[str] = mapped_column(default="America/New_York")
    pick_clock_seconds: Mapped[int] = mapped_column(default=90)
    num_rounds: Mapped[int] = mapped_column(default=15)
    num_teams: Mapped[int] = mapped_column(default=12)
    current_pick_num: Mapped[int] = mapped_column(default=0)
    pick_deadline_epoch: Mapped[float | None] = mapped_column(default=None)  # epoch float
    draft_order: Mapped[list] = mapped_column(JSONB, default=list)  # [team_id, ...]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))

class DraftPick(Base):
    __tablename__ = "draft_picks"
    __table_args__ = (
        UniqueConstraint("draft_id", "pick_num"),
        UniqueConstraint("draft_id", "player_id"),  # player can be drafted once
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    pick_num: Mapped[int]
    round: Mapped[int]
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[str]
    is_auto_pick: Mapped[bool] = mapped_column(default=False)
    picked_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
    reactions: Mapped[dict] = mapped_column(JSONB, default=dict)
    # reactions schema: {"fire": ["user_id_1"], "laugh": ["user_id_2", "user_id_3"], ...}

class DraftQueue(Base):
    __tablename__ = "draft_queue"
    __table_args__ = (
        UniqueConstraint("draft_id", "user_id", "player_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[str]
    position: Mapped[int]  # sort order (1-indexed); client reorders by updating all positions
    added_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))

class DraftChatMessage(Base):
    __tablename__ = "draft_chat_messages"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))

class UserDraftRanking(Base):
    __tablename__ = "user_draft_rankings"
    __table_args__ = (
        UniqueConstraint("draft_id", "user_id", "player_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_id: Mapped[str]
    rank: Mapped[int]
    source: Mapped[str] = mapped_column(default="fantasycalc")  # fantasycalc|csv|manual
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
```

Key indices for migration:
- `draft_picks(draft_id, pick_num)` — lookup by pick order
- `draft_picks(draft_id, player_id)` — player availability check
- `draft_queue(draft_id, user_id, position)` — per-user queue sorted by position
- `user_draft_rankings(draft_id, user_id, rank)` — per-user sorted rankings
- `draft_chat_messages(draft_id, created_at)` — chronological chat

---

## Redis Key Conventions (Claude's Discretion)

```
draft:{draft_id}:events           Stream — all draft events (XADD/XRANGE)
draft:{draft_id}:state            String — "pending" | "live" | "paused" | "complete"
draft:{draft_id}:current_pick     String — current pick number (int as string)
draft:{draft_id}:pick_deadline    String — epoch float (e.g., "1720000090.123")
draft:{draft_id}:pick_lock        String — sid of lock holder (SETNX, TTL 5s)
draft:{draft_id}:available        Set — player_id strings of undrafted players
```

Extend `CacheKey` class in `backend/app/core/cache.py`:
```python
@staticmethod
def draft_events(draft_id: str) -> str:
    return f"draft:{draft_id}:events"

@staticmethod
def draft_state(draft_id: str) -> str:
    return f"draft:{draft_id}:state"

@staticmethod
def draft_current_pick(draft_id: str) -> str:
    return f"draft:{draft_id}:current_pick"

@staticmethod
def draft_deadline(draft_id: str) -> str:
    return f"draft:{draft_id}:pick_deadline"

@staticmethod
def draft_lock(draft_id: str) -> str:
    return f"draft:{draft_id}:pick_lock"

@staticmethod
def draft_available(draft_id: str) -> str:
    return f"draft:{draft_id}:available"
```

---

## Socket.IO Event Naming Conventions (Claude's Discretion)

| Direction | Event | Payload | Notes |
|-----------|-------|---------|-------|
| Server → room | `pick_started` | `{pick_num, team_id, team_name, deadline}` | Every new pick slot |
| Client → server | `pick` | `{player_id}` | Pick submission |
| Server → room | `pick_confirmed` | `{pick_num, player_id, team_id, is_auto_pick, event_id}` | After DB commit |
| Server → room | `auto_drafted` | `{pick_num, player_id, team_id, event_id}` | Auto-pick fired |
| Client → server | `chat` | `{message}` | Chat message |
| Server → room | `chat_message` | `{user_id, name, message, created_at}` | Broadcast |
| Client → server | `react` | `{pick_num, emoji}` | Emoji reaction on a pick |
| Server → room | `reaction_added` | `{pick_num, reactions}` | Full reactions dict |
| Client → server | `reconnect` | `{last_event_id}` | On socket reconnect |
| Server → client | `replay_event` | `{id, type, ...fields}` | Batch replay |
| Server → room | `draft_paused` | `{}` | Commissioner pause |
| Server → room | `draft_resuming` | `{countdown: 5}` | Resume countdown |
| Server → room | `draft_started` | `{pick_num: 1, team_id, deadline}` | Draft begins |
| Server → room | `draft_complete` | `{}` | Last pick made |
| Server → room | `member_presence` | `{user_id, online}` | Connect/disconnect |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SSE or long-polling for real-time picks | Socket.IO rooms with Redis adapter | Already established (Phase 0 scaffold) | Already implemented in this project |
| REST snapshot on reconnect | Redis Stream XRANGE replay | D-07 decision | No snapshot endpoint needed; stream is the source of truth |
| Server-side screenshot (wkhtmltoimage, headless Chrome) | `html2canvas` client-side | Settled pattern since ~2018 | No server process; runs in browser; captures live DOM state |
| Consumer groups for event replay | Plain XRANGE | — | Consumer groups are for competing worker consumers; replay is a read-only fan-out |
| pytz for timezone handling | `zoneinfo` (Python stdlib since 3.9) | Python 3.9+ (project requires 3.11+) | No external pytz dependency needed for ICS generation |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: FastAPI has deprecated these in favor of lifespan context managers (`@asynccontextmanager`). Current code uses the deprecated form. Phase 4 should not introduce new uses of `@app.on_event`. Existing deprecations are out of scope for this phase.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `usePickClock` hook with 250ms `setInterval` is sufficient for smooth countdown display | Pattern 4 | Could cause perceived jitter; use `requestAnimationFrame` instead if jitter is reported |
| A2 | Snake draft order algorithm (odd rounds L→R, even rounds R→L) is universally correct | Pattern 10 | Some platforms use "third-round reversal" or other variants; commissioner import should override order |
| A3 | ADP grade percentile boundaries (A+ <15%, A <30%, B <45%, C <60%, D <80%, F else) | Pattern 11 | Grade distribution may feel off for small leagues; adjust thresholds after user feedback |
| A4 | `useSortable` from `@dnd-kit/sortable` v10 maintains the same API as v9 for vertical list reorder | Standard Stack | v10 is `@dnd-kit/react` rewrite (hooks-based); if API differs significantly, use old v9 pattern from v6 |
| A5 | `html2canvas` correctly renders JetBrains Mono web font loaded via Google Fonts | Pitfall 4 | Web fonts may not be captured; may need `document.fonts.ready` await before capture |
| A6 | Redis `available` SET initialized from FantasyCalc player pool is sufficient (no need for NFL roster cross-reference) | Pattern 5 | If FantasyCalc doesn't cover all draftable players (K, DEF), need supplemental source |

---

## Open Questions

1. **Draft order import from host platform (D-12, Step 3)**
   - What we know: Sleeper API exposes draft order; Yahoo and ESPN likely do too but not verified
   - What's unclear: Exact API endpoint and response format for Yahoo/ESPN draft order
   - Recommendation: Implement manual + randomize first (covers most users); add import-from-host as a stretch in the last wave

2. **@dnd-kit/sortable v10 API compatibility**
   - What we know: `@dnd-kit/sortable` v10 in package.json; existing code uses v9 API (Phase 2 uses `@dnd-kit/core` 6.3.1)
   - What's unclear: v10 is the new `@dnd-kit/react` package rewrite; `useSortable` may require `index` prop in addition to `id`
   - Recommendation: Check the existing `LineupCard.tsx` drag implementation pattern; replicate exactly for queue reorder

3. **Player pool for availability SET initialization**
   - What we know: FantasyCalc covers top ~460 dynasty / ~200 redraft players; Sleeper player pool covers all NFL players
   - What's unclear: Should the available SET be Sleeper's full player pool or filtered to "draftable" positions?
   - Recommendation: Filter to fantasy-relevant positions (QB, RB, WR, TE, K, DEF) from Sleeper player pool; initialize at draft start

4. **Royalty-free audio files for pick.mp3 and your-turn.mp3**
   - What we know: Must be pre-bundled, ≤100KB each, no external CDN (D-06)
   - What's unclear: Specific audio file selection is Claude's discretion (per CONTEXT.md)
   - Recommendation: Use Freesound.org CC0 licensed short chime files; encode to MP3 at 64kbps ≤ 100KB

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All backend | ✓ | 3.x (project requires 3.11+) | — |
| `python-socketio` | `/draft` namespace | ✓ | 5.16.3 [VERIFIED: pip] | — |
| `redis.asyncio` | Streams, deadline, lock | ✓ | 8.0.1 [VERIFIED: pip] | — |
| `arq` | Auto-draft timer | ✓ [VERIFIED: workers/tasks.py import] | installed | — |
| `fastapi-mail` | ICS email delivery | ✓ | 1.6.5 [VERIFIED: pip] | — |
| `icalendar` | ICS file generation | ✗ | NOT installed | None — must add to pyproject.toml |
| `socket.io-client` | Frontend namespace | ✓ | ^4.7.5 (in package.json) | — |
| `@dnd-kit/sortable` | Queue reorder, draft order | ✓ | ^10.0.0 (in package.json) | — |
| `html2canvas` | PNG recap export | ✗ | NOT in package.json | None — must add |
| Playwright (`@playwright/test`) | E2E draft tests | ✓ | e2e/ configured [VERIFIED: e2e/playwright.config.ts] | — |
| PostgreSQL | Draft models | ✓ | Already running (Phase 0 docker-compose) | — |
| Redis | Streams, real-time | ✓ | Already running (Phase 0 docker-compose) | — |

**Missing dependencies with no fallback:**
- `icalendar>=7.2.0` — add to `[project] dependencies` in `backend/pyproject.toml`
- `html2canvas@^1.4.0` — add to `frontend/package.json` dependencies

**Missing dependencies with fallback:**
- None in this phase.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 + pytest-asyncio 0.23.0 (backend) |
| E2E Framework | Playwright (`@playwright/test`) — `e2e/` directory configured |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd backend && pytest tests/test_draft_service.py tests/test_draft_models.py -x -q` |
| Full suite command | `cd backend && pytest tests/ -q` + `cd e2e && npx playwright test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DR-01 | ICS file generated with correct timezone and duration | unit | `pytest tests/test_draft_service.py::test_build_draft_ics -x` | ❌ Wave 0 |
| DR-02 | Snake draft order: pick 1 → team 0, pick 12 → team 11, pick 13 → team 11 (snake back) | unit | `pytest tests/test_draft_service.py::test_snake_pick_to_slot -x` | ❌ Wave 0 |
| DR-03 | CSV import → player_id match via PlayerCrossMap fuzzy | unit | `pytest tests/test_draft_service.py::test_csv_rankings_import -x` | ❌ Wave 0 |
| DR-04 | Tier divider auto-calculation: >15 rank delta = new tier | unit | `pytest tests/test_draft_service.py::test_tier_boundaries -x` | ❌ Wave 0 |
| DR-07 | Pick propagates: Socket.IO namespace connect, pick, pick_confirmed received | integration | `pytest tests/test_draft_namespace.py::test_pick_propagates -x` | ❌ Wave 0 |
| DR-08 | Auto-draft: queue non-empty → top queued; queue empty → ADP+need | unit | `pytest tests/test_draft_service.py::test_auto_draft_selection -x` | ❌ Wave 0 |
| DR-08 | Positional need bonus prevents selecting 6th WR over QB | unit | `pytest tests/test_draft_service.py::test_positional_need_weighting -x` | ❌ Wave 0 |
| DR-09 | Commissioner pause emits draft_paused; non-commissioner pause rejected | integration | `pytest tests/test_draft_namespace.py::test_commissioner_pause -x` | ❌ Wave 0 |
| DR-13 | ADP grade computation: A+/A/B/C/D/F by percentile | unit | `pytest tests/test_draft_service.py::test_adp_grade_computation -x` | ❌ Wave 0 |
| DR-15 | Redis stream write (XADD) + replay (XRANGE exclusive) correct | unit | `pytest tests/test_draft_service.py::test_redis_stream_replay -x` | ❌ Wave 0 |
| DR-15 | Reconnect replays missed events and board state is correct | E2E | `npx playwright test e2e/tests/uat-10-draft-reconnect.spec.ts` | ❌ Wave 0 |
| DR-07 DR-09 | Full draft flow: schedule → lobby → pick × 3 → auto-draft → pause → resume | E2E | `npx playwright test e2e/tests/uat-11-draft-flow.spec.ts` | ❌ Wave 0 |
| DR-07 | Pick propagation < 500ms (p99) | perf | Manual timing in Playwright `expect(page).toHaveReceivedEvent` with timestamp | Manual |

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/test_draft_service.py tests/test_draft_namespace.py -x -q`
- **Per wave merge:** `cd backend && pytest tests/ -q` (full backend suite)
- **Phase gate:** Full suite green + `cd e2e && npx playwright test` passing before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_draft_service.py` — snake order, ICS, auto-draft selection, tier boundaries, ADP grade, XRANGE exclusive, positional need weighting
- [ ] `backend/tests/test_draft_namespace.py` — Socket.IO `/draft` connect/disconnect, pick, commissioner-only events
- [ ] `backend/tests/conftest.py` — extend `mock_redis` with `xadd`, `xrange`, `sadd`, `srem`, `sismember`, `set(nx=True)` mock methods for draft tests
- [ ] `e2e/tests/uat-10-draft-reconnect.spec.ts` — disconnect mid-draft, reconnect, verify board state
- [ ] `e2e/tests/uat-11-draft-flow.spec.ts` — full happy path: schedule → lobby → picks → recap
- [ ] `icalendar>=7.2.0` — add to `pyproject.toml`
- [ ] `html2canvas@^1.4.0` — add to `frontend/package.json`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | JWT verification in `on_connect(auth)` — refuse connection if token invalid or expired |
| V3 Session Management | yes | Socket.IO `save_session`/`get_session` per SID; session cleared on disconnect |
| V4 Access Control | yes | Commissioner-only events (pause, resume, start, randomize order) verified server-side; `LeagueMember.role == "commissioner"` check on every privileged event |
| V5 Input Validation | yes | Pydantic schema on all REST draft endpoints; `player_id` validated against `draft:{id}:available` SET before confirming pick |
| V6 Cryptography | no | No new cryptographic operations in Phase 4 |

### Known Threat Patterns for Real-Time Draft

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Forged pick submission (user picks for another team) | Spoofing | Server derives `team_id` from authenticated `user_id` via `LeagueMember` join — never trust client-provided `team_id` |
| Duplicate pick submission (double-click or replay) | Tampering | `UniqueConstraint("draft_id", "player_id")` on `draft_picks`; `SETNX` pick lock |
| Commissioner impersonation on Socket.IO | Elevation of Privilege | Role check on every privileged event in namespace handler, not just at connect time |
| Stale ICS invite used to join expired draft | Spoofing | Draft room checks `Draft.status != "pending"` at lobby entry; expired invites don't grant access |
| Redis Stream poisoning | Tampering | Stream is written server-side only; no client endpoint writes directly to Redis |
| Auto-draft timer misfiring on stale job | Denial of Service | Idempotent guard: arq task checks `current_pick_num` matches expected; exits if stale |

---

## Sources

### Primary (HIGH confidence)

- `/miguelgrinberg/python-socketio` (Context7) — AsyncNamespace class, rooms, emit, auth in on_connect, namespace registration
- `/websites/redis_readthedocs_io_en_stable` (Context7) — XADD, XRANGE, SETNX NX EX, SREM, SADD, SISMEMBER API signatures
- `/python-arq/arq` + `/websites/arq-docs_helpmanual_io` (Context7) — `enqueue_job` `_defer_until`, `_job_id` uniqueness, `allow_abort_jobs`, `_expires`
- `/collective/icalendar` (Context7) — `Calendar.new()`, `Event.new()`, `add_missing_timezones()`, `ZoneInfo` timezone pattern
- `/niklasvh/html2canvas` (Context7) — `html2canvas(element, opts)`, `canvas.toBlob()`, `useCORS`, `scale`
- `/clauderic/dnd-kit` (Context7) — `useSortable` hook, `DndContext`, vertical list reorder pattern
- Codebase inspection — `main.py` (Socket.IO scaffold), `cache.py` (CacheKey pattern), `workers/tasks.py` (arq WorkerSettings pattern), `conftest.py` (test infrastructure), `auth.ts` (Zustand persist pattern), `App.tsx` (`/draft` route), `e2e/playwright.config.ts` (Playwright setup)
- `pip index versions` / `npm view` — version verification for all packages

### Secondary (MEDIUM confidence)

- `pip show` output — confirmed installed package versions (python-socketio 5.16.3, redis 8.0.1, fastapi-mail 1.6.5)
- `package.json` inspection — socket.io-client ^4.7.5, @dnd-kit/core ^6.3.1, @dnd-kit/sortable ^10.0.0

### Tertiary (LOW confidence — see Assumptions Log)

- Pick clock 250ms setInterval approach — standard pattern but not verified in official Socket.IO docs
- ADP grade percentile thresholds — [ASSUMED] reasonable defaults; not from official fantasy analytics source
- Snake order algorithm correctness for all edge cases — [ASSUMED] standard implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all installed packages verified via pip/package.json; new packages verified via npm view / pip index
- Architecture patterns: HIGH — Socket.IO namespace, Redis Stream, arq deferred job patterns all verified against Context7 official docs
- Model schemas: MEDIUM — reasonable designs for the problem; exact column choices may need adjustment during implementation
- ADP grade algorithm: LOW — thresholds are assumed; no official fantasy analytics source for grade boundaries
- Pitfalls: HIGH — each verified against official docs or codebase behavior

**Research date:** 2026-07-01
**Valid until:** 2026-08-01 (packages are stable; Redis/Socket.IO APIs do not change frequently)
