# Architecture

This document captures the recommended technical architecture for Fantasy Football Hub. For every meaningful decision we present 2–3 options, the trade-offs, and the recommendation. The recommendations are non-binding until each is voted in a `design-vote` issue and the result is recorded here.

---

## 1. Goals and Constraints

### Goals

1. **Real-time everything in the draft room** — sub-500ms pick propagation to all participants
2. **Snappy non-draft UX** — most reads must come from cache; cold-load tolerable, warm-load fast
3. **Survive host platform rate limits** — never make the user the one who hits a Yahoo rate-limit wall
4. **Multi-tenant by user** — each user has their own connections; one user must never see another's data
5. **Familiar stack** — overlap with `fantasybbleague` so context-switching cost is low
6. **One developer can run the full stack locally** in under 10 minutes

### Constraints

- Budget: indie scale. No GCP/AWS account expansion that costs more than ~$50/mo at MVP.
- Team: 1–2 developers. No room for ops complexity.
- Reliability tier: best-effort. Outages during the off-season are fine. Outages during draft night are not.

---

## 2. Tech Stack Decisions

For each decision: **Option A**, **Option B**, sometimes **C**, then **Recommendation**.

### 2.1 Backend Language and Framework

| Option | Pros | Cons |
|--------|------|------|
| **A. Python + FastAPI** | Async-native; matches `fantasybbleague`; rich data libs (Pandas, NumPy); FastAPI docs and validation are excellent | GIL limits some concurrency patterns; WebSocket story relies on `python-socketio` |
| **B. Node.js + NestJS** | Strong WebSocket and real-time story; single language with frontend; TypeScript end-to-end | Less natural for analytics-heavy code; we would be re-learning patterns Paul already has in Python |
| **C. Go + Gin/Echo** | Best raw real-time performance; easy deploys (single binary); great concurrency | Smaller ML/analytics ecosystem; longer ramp for a 2-person team; less existing code to crib from |

**Recommendation: A (Python + FastAPI).** Overlap with `fantasybbleague` is the deciding factor. Real-time concerns are handled via `python-socketio` + Redis adapter, which has been battle-tested at scale.

### 2.2 Frontend Framework

| Option | Pros | Cons |
|--------|------|------|
| **A. React 18 + Vite + TypeScript** | Huge ecosystem; React Query is excellent for our caching pattern; Tailwind plays well; matches Paul's recent projects | More boilerplate than alternatives |
| **B. SvelteKit** | Smaller bundles; built-in SSR if we need it; less boilerplate; reactivity model is excellent for live data | Smaller talent pool; fewer "stolen" components from broader ecosystem |
| **C. Next.js (React + SSR)** | Great DX; built-in API routes; image optimization; SSR for SEO | We do not need SEO for an authenticated app; SSR adds complexity we do not benefit from |

**Recommendation: A (React 18 + Vite + TypeScript).** SSR is unnecessary for an authenticated app, and Vite is fast enough that the dev loop is excellent. React Query handles cache fan-in elegantly.

### 2.3 Styling

| Option | Pros | Cons |
|--------|------|------|
| **A. Tailwind CSS** | Fast iteration; design system via config; works well with component libs | Class strings get long without component extraction |
| **B. CSS Modules + custom design tokens** | More traditional separation of concerns | Slower iteration; we end up rebuilding what Tailwind already provides |
| **C. Stitches / Vanilla Extract (CSS-in-TS)** | Type-safe styles | Smaller ecosystem; learning curve |

**Recommendation: A (Tailwind).** Pair with `shadcn/ui` (copy-in components, not a dep) for primitives. The dark draft-room aesthetic is achievable with a custom Tailwind theme.

### 2.4 Real-Time Layer

| Option | Pros | Cons |
|--------|------|------|
| **A. python-socketio + Redis adapter** | Excellent fan-out via Redis pub/sub; rooms map naturally to "league-N" and "draft-N"; works across multiple backend instances | Adds Redis as a hard dependency for real-time |
| **B. Raw WebSockets via FastAPI** | Lightest weight; no extra protocol layer | We rebuild rooms, reconnection, message acking, namespaces |
| **C. Pusher or Ably (managed)** | Zero ops for real-time; SDKs everywhere | Cost scales with usage; lock-in; less control during draft-night incidents |

**Recommendation: A (python-socketio + Redis).** Redis is on the stack anyway for caching. The "rooms" abstraction maps perfectly to leagues and drafts.

### 2.5 Video / Audio for Draft Room

| Option | Pros | Cons |
|--------|------|------|
| **A. Daily.co** | Managed WebRTC; clean React SDK; pay-per-minute; SFU; recording optional | Cost per participant-minute; another vendor |
| **B. Twilio Video** | Mature; broader product suite | More expensive; heavier SDK |
| **C. Self-hosted (Jitsi, LiveKit)** | No per-minute cost | Operationally heavy; TURN servers, scaling, debugging at draft time |

**Recommendation: A (Daily.co).** Single most important property: it works without us being on-call for it. Audio-only fallback is built-in. Estimated cost: ~$0.004/participant-minute → a 12-team, 4-hour draft costs ~$11.

### 2.6 Primary Database

| Option | Pros | Cons |
|--------|------|------|
| **A. PostgreSQL 16** | Relational fit; JSONB for scoring rules; row-level security if we ever need it; mature; cheap | Slightly more setup than SQLite |
| **B. SQLite** | Trivially simple; zero ops | Multi-tenant concurrency limits; harder to run multiple app processes |
| **C. MongoDB** | Schema flexibility for varied scoring | We do not actually have unstructured data; we have varied schemas, which is different |

**Recommendation: A (PostgreSQL 16).** Despite the global preference for SQLite on small projects, the real-time + multi-process draft room makes Postgres the right call. We can still hold to "as much in JSONB as makes sense" for things like scoring rules.

### 2.7 Cache

| Option | Pros | Cons |
|--------|------|------|
| **A. Redis** | TTL, pub/sub, rate-limit counters, session store; one piece of infra serves multiple jobs | One more service to run |
| **B. In-process + on-disk pickle** | Mirrors `fantasybbleague` exactly | Does not survive process restarts; breaks the moment we run more than one app instance |
| **C. Memcached** | Simple; fast | No pub/sub; no persistence; we lose half the value |

**Recommendation: A (Redis).** It is the right answer for cache, queues, pub/sub, and rate limiting. One Redis instance covers a lot of ground.

### 2.8 Background Jobs

| Option | Pros | Cons |
|--------|------|------|
| **A. Celery + Redis broker** | Most common Python option; well documented | Heavier than we need for simple scheduled syncs |
| **B. APScheduler + custom workers** | Lightweight; in-process is fine for MVP | Need to migrate if we ever scale out |
| **C. arq (asyncio-native queue, Redis-backed)** | Async-native; tiny footprint; great for our scale | Smaller community |

**Recommendation: C (arq) for MVP.** Async-native fits FastAPI; minimal additional dependencies. Revisit Celery if we hit operational complexity that arq does not handle.

### 2.9 Auth

| Option | Pros | Cons |
|--------|------|------|
| **A. App-level Auth0 / Clerk** | Hosted, secure, fast to integrate | Cost scales; one more vendor |
| **B. Self-hosted JWT with `python-jose` + Argon2 password hashing** | No vendor; full control; no monthly fees | We write the recovery, verification, and rate-limit code |
| **C. Supabase Auth** | Free tier; OAuth providers built-in | Implies we are also using Supabase Postgres, which we are not |

**Recommendation: B (self-hosted JWT)** with email + Google OAuth. We are already comfortable building this. Use the OWASP cheat sheet as our checklist. **Host-platform OAuth is separate** — that is per-platform (Yahoo, ESPN) and is for *their* API, not our user auth.

### 2.10 Hosting

| Option | Pros | Cons |
|--------|------|------|
| **A. Single Digital Ocean droplet (MVP) → multiple Fly.io machines (V1)** | Matches existing infra; cheap; easy debugging | Eventually we will outgrow a single droplet |
| **B. Render** | Auto-deploy from GitHub; managed Postgres + Redis; simple | More expensive than DO at scale; less control |
| **C. AWS (ECS or Lightsail)** | Most options long-term | Operationally heavy for a 2-person team |

**Recommendation: A.** Start with one DO droplet (Postgres, Redis, app on same box), move Postgres and Redis to managed services when traffic justifies, and split app + worker when async load demands it. PM2 manages the Node process (none yet) and a separate systemd unit runs the Python app.

---

## 3. Data Model (Sketch)

The full schema lives in a future `/db/schema.sql` once we are building. This section gives the shape so we can reason about caching and ownership.

```
users
  id, email, password_hash, created_at, last_login_at

oauth_credentials
  id, user_id, platform, encrypted_refresh_token, encrypted_access_token,
  access_token_expires_at, last_validated_at, scope

leagues
  id, host_platform, host_league_id, season, name, scoring_rules JSONB,
  roster_format JSONB, draft_type, keeper_flag, dynasty_flag, last_synced_at

league_members (the bridge between users and leagues)
  user_id, league_id, host_team_id, role  -- role: owner, commissioner, viewer

teams
  id, league_id, host_team_id, name, owner_user_id (nullable), abbreviation

rosters
  team_id, week, snapshot JSONB, last_synced_at

players
  id, host_id_yahoo, host_id_sleeper, host_id_espn, name, position,
  nfl_team, status, last_updated

projections
  player_id, week, source, projected_points, confidence, factors JSONB

drafts
  id, league_id, type, state, scheduled_at, started_at, completed_at,
  pick_clock_seconds, order JSONB

picks
  draft_id, round, slot, overall, team_id, player_id, made_at, was_autopick,
  duration_seconds

trades
  id, league_id, proposer_team_id, receiver_team_id, status, created_at,
  decided_at, expires_at, ai_summary

trade_assets
  trade_id, side, asset_type, player_id (nullable), faab_amount (nullable),
  draft_pick (nullable JSONB)

chat_messages
  id, scope_type (league|draft), scope_id, user_id, body, created_at

notifications
  id, user_id, category, channel, payload JSONB, sent_at, read_at
```

Key design points:

- `leagues` is **deduplicated by `(host_platform, host_league_id, season)`** so two users in the same league share the underlying record.
- `oauth_credentials.encrypted_*` columns store ciphertext encrypted with a per-user envelope key, which itself is wrapped by an app-level master key from env config.
- `players.host_id_*` allows joining identities across platforms. We will need a small ID-mapping table for edge cases (rookies before host platforms assign IDs).
- `rosters.snapshot` is a JSONB blob to avoid normalizing the volatile shape of weekly lineups.

---

## 4. Data Flow Diagrams

### 4.1 League Connection (Sleeper, no OAuth)

```
+--------+         +-------------+         +------------+         +----------+
| Browser| --POST->| FastAPI     | --GET-->| Sleeper API|         | Postgres |
| /react |         | /connect    | <-200-- | (read-only)|         |          |
+--------+         +-------------+         +------------+         +----------+
                          |                                            ^
                          | upsert league + member + roster            |
                          +--------------------------------------------+
                          |
                          | SET league:{id}:settings (TTL 6h)
                          v
                      +---------+
                      |  Redis  |
                      +---------+
```

### 4.2 Lineup Recommendation Read

```
Browser  --GET /api/teams/{id}/lineup?week=N-->  FastAPI
                                                   |
                                  cache HIT?  --YES-> return cached lineup
                                                   |  (Redis: lineup:{team}:{week}, TTL 30m)
                                                   |
                                                   v  cache MISS
                                                   |
                                                   |--> query Postgres for roster snapshot
                                                   |--> query Postgres for projections
                                                   |--> compute optimal lineup (deterministic)
                                                   |--> SET cache
                                                   |
                                                   v
                                                return computed lineup
```

### 4.3 Draft Room Pick (Real-Time Fan-Out)

```
   User A           FastAPI / socketio        Redis pub/sub      Users B..N
   ------           ------------------        --------------     ----------
     |                      |                       |                |
     | emit "make_pick" --> |                       |                |
     |                      | validate pick         |                |
     |                      | INSERT picks row      |                |
     |                      | advance draft state   |                |
     |                      | -- publish --------> |                |
     |                      |                       | -- broadcast ->| emit "pick_made"
     |                      |                       |                |
     |                      | -- ack to A --------- |                |
     |                                                                |
     v                                                                v
   sees own pick                                                   sees pick on board
   confirmed (< 200ms)                                             (< 500ms p99)
```

Notes:
- All draft writes go through a single FastAPI process at a time *per draft room*, enforced by a Redis lock keyed on `draft:{id}:lock`. This makes pick ordering trivially serializable.
- The Redis pub/sub adapter for socketio fan-outs the broadcast so multiple FastAPI instances stay in sync; the lock ensures only one of them mutates state.

### 4.4 Trade Evaluation

```
   Browser --POST /api/trades/evaluate-->  FastAPI
                                              |
                                              |--> load both rosters from cache
                                              |--> load season projections from cache
                                              |--> load schedules from cache
                                              |--> compute value totals (deterministic)
                                              |--> if AI summary requested:
                                              |       POST to LLM provider with structured prompt
                                              |       (cache prompt hash -> summary in Redis 24h)
                                              |--> return composite payload
```

---

## 5. Caching Strategy

The cache is the system of record between syncs. The contract is:

> If it is in cache and not expired, trust it. If it is not, fetch from upstream, then update cache. **Writes invalidate.**

### 5.1 What to Cache

| Key pattern | What it holds | TTL | Invalidation trigger |
|-------------|---------------|-----|---------------------|
| `league:{id}:settings` | Scoring, roster format, league name | 6 hours | Manual refresh; commissioner change |
| `league:{id}:rosters:{week}` | All team rosters for a given week | 30 minutes (live), 24h (past weeks) | Roster move; weekly rollover |
| `league:{id}:members` | List of users in this league | 6 hours | New user connects this league |
| `player:{id}:profile` | Static player info, team, position | 24 hours | Trade/release news (event-driven) |
| `player:{id}:projection:{week}` | Per-week projection | 6 hours during game week, 1 hour Sunday | News event; injury report |
| `player:{id}:news` | Recent news items | 15 minutes | New news ingested |
| `lineup:{team}:{week}` | Computed optimal lineup | 30 minutes | Roster change on this team |
| `trade:{hash}` | AI summary for a specific trade composition | 24 hours | Player news affecting any participant |
| `draft:{id}:state` | Live draft state, used as warm cache for reconnects | Until draft ends + 7 days | Every pick |
| `ratelimit:{platform}:{user}` | Sliding-window counter for upstream rate limits | Window size | N/A (sliding) |

### 5.2 Invalidation Strategy

Three patterns, in order of preference:

1. **Event-driven (best)** — when a roster move webhook arrives, delete the affected keys directly. We will model webhook receivers per platform where available (Sleeper has none, Yahoo has limited, ESPN has none — so this is mostly Sleeper polling-as-webhook).
2. **Write-through (next best)** — when our own app performs a write (lineup change, trade accept), the same handler invalidates derived keys before returning.
3. **TTL-based (fallback)** — short TTLs keep us honest when we cannot capture an event.

We will **never** rely on long TTLs as a primary correctness mechanism. They are only the backstop.

### 5.3 Cache Stampede Protection

For hot keys (e.g. `player:{id}:projection:{week}` on Sunday morning), we will use a **lock + serve-stale** pattern:

```
get key -> if hit, return
        -> if miss:
              try acquire short Redis lock for "refresh:{key}"
              if locked, fetch fresh + set + release
              if not locked, return last-good value (if any) and do not fetch
```

This is implemented as a small helper used by all cache reads.

### 5.4 Rate-Limit Budgets

Per-platform sliding-window counters using Redis sorted sets. Conservative limits we will enforce ourselves (well below documented platform ceilings):

| Platform | Limit we enforce | Reason |
|----------|------------------|--------|
| Yahoo Fantasy | 50 reqs / user / hour | Yahoo is the strictest; preserves headroom |
| Sleeper | 100 reqs / user / minute | Sleeper is permissive but we still rate-limit to be polite |
| ESPN | 20 reqs / user / minute | ESPN cookies are fragile; we keep traffic low |
| NFL.com | 30 reqs / user / minute | Conservative until we measure |

When a user trips a rate limit, the API returns a 429 with `Retry-After`, the UI shows a soft toast, and the cached value is returned instead.

---

## 6. Real-Time Design

### 6.1 Channels and Rooms

Socket.IO namespaces:

- `/league` — chat, trade pings, lineup alerts, scoped per league
- `/draft` — draft-room events, scoped per draft

Within each namespace, rooms are keyed:

- `league:{id}` — all members of a league
- `league:{id}:user:{user_id}` — private channel to a single user
- `draft:{id}` — all participants in a draft
- `draft:{id}:user:{user_id}` — private channel for "you're on the clock" events

### 6.2 Message Types

```
# Draft namespace
pick_made              { round, slot, overall, team_id, player_id, made_at }
on_the_clock           { team_id, ends_at }
clock_paused           { paused_by_user_id }
clock_resumed          { resumes_at }
auction_nomination     { player_id, nominated_by_team_id, ends_at }
auction_bid            { player_id, team_id, amount, ends_at }
auction_sold           { player_id, team_id, amount }
chat_message           { user_id, body, created_at }
pick_reaction          { pick_overall, user_id, emoji }
draft_ended            { ended_at }

# League namespace
trade_proposed         { trade_id, from_team_id, to_team_id, summary }
trade_status_changed   { trade_id, new_status, actor_user_id }
lineup_alert           { team_id, week, severity, body }
injury_alert           { player_id, status, source }
```

### 6.3 Reconnect and Resume

Each client tracks the last event ID it has seen. On reconnect, it emits `resume_from { last_event_id }`. The server replays missed events from a Redis stream (`stream:draft:{id}` and `stream:league:{id}`) up to that point. Streams are capped at 7 days for league events and "until 24h after draft ends" for draft events.

### 6.4 Authoritative State Snapshot

On every reconnect, before replaying events, the server sends a full state snapshot for the room. This makes reasoning about consistency trivial: snapshot then replay. Clients should treat the snapshot as truth and ignore any earlier in-memory state.

---

## 7. Auth Architecture

### 7.1 Two Distinct Auth Domains

Important to separate clearly:

1. **App auth** — how a user signs into Fantasy Football Hub. JWT (access + refresh) with email/password or Google OAuth as the identity provider.
2. **Host-platform auth** — how Fantasy Football Hub talks to Yahoo, ESPN, etc. on the user's behalf. Per-platform OAuth tokens, stored encrypted per `oauth_credentials` table.

A user might have one app-auth identity and zero, one, or many host-platform credential records.

### 7.2 Credential Storage

- Master key in env (`MASTER_ENCRYPTION_KEY`), 256-bit, generated at deploy time and never logged.
- Each user has an envelope key, wrapped with the master key, stored alongside the user row.
- Refresh tokens for host platforms are encrypted with the user's envelope key and stored in `oauth_credentials.encrypted_refresh_token`.
- Access tokens are short-lived; we always refresh just-in-time and cache for the documented lifetime minus 60 seconds.
- Rotation: when a refresh token is used, the response often includes a new refresh token. We rotate immediately and write the new ciphertext.

### 7.3 Session Strategy

- Access tokens: 15-minute JWT, HS256 signed, in an `Authorization: Bearer` header.
- Refresh tokens: 30-day rotating opaque tokens, stored hashed in `sessions` table, sent as `httpOnly; Secure; SameSite=Lax` cookies.
- Sliding session: any refresh extends the 30-day window.

---

## 8. Mobile and Responsive Strategy

- **Single React codebase** with breakpoint-driven layouts. We do not ship a separate mobile app in V1.
- Three breakpoints: phone (`< 640px`), tablet (`640–1024px`), desktop (`> 1024px`).
- Touch-first interactions for any swap/reorder UX (drag-and-drop must work with pointer events, not just mouse).
- Service worker for offline reads of cached state (V1) so that loading the dashboard on a flaky Sunday morning connection still works.
- PWA install prompt after first successful league connection. We deliberately defer native apps.

---

## 9. Observability

A small observability footprint, sized for a 2-person project:

- **Logs**: structured JSON to stdout; `journald` on the droplet; rotate after 7 days. Sentry for errors.
- **Metrics**: a small Prometheus-style endpoint scraped by Grafana Cloud free tier. Key dashboards: request latency, cache hit rate, upstream platform errors, draft-room latency p99.
- **Tracing**: deferred. Sentry's "performance" view is enough at our scale.
- **Alerting**: PagerDuty-free; we use a Discord webhook for warning/critical events.

---

## 10. Security Posture (Summary)

A full security review will happen before V1 ships. The MVP-level commitments:

- All credentials encrypted at rest with documented key management
- TLS everywhere; HSTS preload after V1 stabilizes
- Input validation via Pydantic on every endpoint
- CSRF protection on cookie-bearing endpoints; SameSite=Lax cookies as the second line
- Audit log table for sensitive actions (credential add/remove, password change, league disconnect)
- Rate limiting per user on all write endpoints (10 req/sec burst, 100 req/min sustained)
- Dependency scanning via `pip-audit` and `npm audit` in CI; fail the build on high-severity findings

---

## 11. Open Architecture Questions

These should each become a `design-vote` issue.

1. **LLM provider for trade analysis.** Claude (Anthropic) vs GPT-4o (OpenAI). Probably Claude given Paul's familiarity, but cost-per-trade and JSON-mode reliability are worth measuring on a sample.
2. **Hosted Postgres vs droplet Postgres for MVP.** Single droplet keeps it cheap; Neon or Supabase removes maintenance.
3. **Sleeper has the best public API but the smallest user share.** Do we make Sleeper the "demo without auth" path for marketing reasons?
4. **Do we ship a CLI for power-users?** Same league analytics, terminal-first. Could be 2 days of work and would be loved by a small but vocal slice of users.
5. **Public read-only league pages.** Showcase finished drafts at a shareable URL. Nice viral hook but adds an auth and privacy surface.
