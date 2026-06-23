# Constraints Intel
# Source: ARCHITECTURE.md (SPEC, locked: false)
# Synthesized by gsd-doc-synthesizer

---

## CONSTRAINT-001 — Backend Framework

type: tech-stack
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.1)

Python 3.12 + FastAPI is the chosen backend. Async-native. Matches existing code in the fantasybbleague project, reducing context-switch cost. GIL limitations acknowledged; real-time handled via python-socketio + Redis adapter. Alternatives evaluated: Node.js + NestJS (rejected: analytics ecosystem weaker), Go + Gin/Echo (rejected: smaller ML ecosystem, longer ramp).

---

## CONSTRAINT-002 — Frontend Framework

type: tech-stack
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.2)

React 18 + Vite + TypeScript is the chosen frontend. No SSR — authenticated app does not need it. React Query for cache fan-in. Tailwind CSS for styling (section 2.3). shadcn/ui (copy-in components, not a dependency) for primitives. Alternatives evaluated: SvelteKit (rejected: smaller ecosystem), Next.js (rejected: SSR complexity provides no benefit for an authenticated app).

---

## CONSTRAINT-003 — Styling

type: tech-stack
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.3)

Tailwind CSS paired with shadcn/ui. Dark draft-room aesthetic achievable via custom Tailwind theme. Alternatives evaluated: CSS Modules (rejected: slower iteration), Stitches/Vanilla Extract (rejected: smaller ecosystem).

---

## CONSTRAINT-004 — Real-Time Layer

type: protocol
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.4, 6)

python-socketio + Redis adapter for all real-time communication. Namespaces: /league (chat, trade pings, lineup alerts) and /draft (draft-room events). Rooms keyed as league:{id}, league:{id}:user:{user_id}, draft:{id}, draft:{id}:user:{user_id}. Performance target: sub-500ms pick propagation p99 for all participants. Alternatives evaluated: Raw WebSockets (rejected: rebuild rooms/reconnection/acking/namespaces), Pusher/Ably (rejected: cost scaling, lock-in).

All draft writes go through a single FastAPI process per draft room, enforced by a Redis lock keyed on draft:{id}:lock. This makes pick ordering trivially serializable.

Reconnect strategy: clients track last event ID, emit resume_from {last_event_id} on reconnect, server replays missed events from Redis stream. Server sends a full state snapshot before replay — snapshot is truth, clients discard earlier in-memory state.

---

## CONSTRAINT-005 — Video/Audio Provider

type: api-contract
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.5)

Daily.co for managed WebRTC in the draft room. Pay-per-minute (~$0.004/participant-minute). Estimated cost: ~$11 for a 12-team 4-hour draft. Audio-only fallback built-in. Alternatives evaluated: Twilio Video (rejected: more expensive, heavier SDK), self-hosted Jitsi/LiveKit (rejected: operationally heavy, TURN server complexity).

---

## CONSTRAINT-006 — Primary Database

type: schema
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (sections 2.6, 3)

PostgreSQL 16 is the primary database. Note: the global Paul preference is SQLite for small/medium projects; this is an explicit override because the multi-process draft room and real-time fan-out patterns require Postgres. JSONB used for scoring_rules, roster_format, factors, order, and rosters.snapshot.

Key schema entities: users, oauth_credentials, leagues, league_members, teams, rosters, players, projections, drafts, picks, trades, trade_assets, chat_messages, notifications.

Key design points:
- leagues is deduplicated by (host_platform, host_league_id, season)
- oauth_credentials.encrypted_* stores ciphertext with per-user envelope key wrapped by app-level master key
- players.host_id_* allows cross-platform identity joining (Yahoo, Sleeper, ESPN)
- rosters.snapshot is JSONB to avoid normalizing volatile weekly lineup shape

Full schema deferred to /db/schema.sql when build begins.

---

## CONSTRAINT-007 — Cache Layer

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (sections 2.7, 5)

Redis 7 is the cache layer, also serving pub/sub and rate-limit counters. Single Redis instance covers cache, queues, pub/sub, and rate limiting.

Cache contract: if in cache and not expired, trust it. If not, fetch from upstream, update cache. Writes invalidate.

Cache key TTLs:
- league:{id}:settings — 6 hours; invalidated on manual refresh or commissioner change
- league:{id}:rosters:{week} — 30 minutes (live), 24h (past weeks); invalidated on roster move or weekly rollover
- league:{id}:members — 6 hours; invalidated when new user connects
- player:{id}:profile — 24 hours; invalidated on trade/release news
- player:{id}:projection:{week} — 6 hours during game week, 1 hour on Sunday; invalidated on news event or injury
- player:{id}:news — 15 minutes; invalidated on new news ingestion
- lineup:{team}:{week} — 30 minutes; invalidated on roster change
- trade:{hash} — 24 hours; invalidated on player news affecting any participant
- draft:{id}:state — until draft ends + 7 days; invalidated on every pick
- ratelimit:{platform}:{user} — sliding window size

Invalidation preference order: (1) event-driven, (2) write-through, (3) TTL-based fallback. Long TTLs are never the primary correctness mechanism.

Cache stampede protection: lock + serve-stale pattern for hot keys (attempt acquire short Redis lock for refresh:{key}; if already locked, return last-good value without fetching).

---

## CONSTRAINT-008 — Rate Limit Budgets

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 5.4)

Per-platform sliding-window rate limit counters enforced in Redis. Self-imposed limits (conservative, below platform ceilings):
- Yahoo Fantasy: 50 requests / user / hour
- Sleeper: 100 requests / user / minute
- ESPN: 20 requests / user / minute
- NFL.com: 30 requests / user / minute

When a user trips a rate limit: API returns 429 with Retry-After, UI shows a soft toast, cached value is returned.

---

## CONSTRAINT-009 — Background Jobs

type: tech-stack
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.8)

arq (asyncio-native queue, Redis-backed) for MVP background jobs. Async-native fit with FastAPI; minimal additional dependencies. Revisit Celery if operational complexity exceeds arq's capability. Alternatives evaluated: Celery + Redis (rejected: heavier than needed for MVP), APScheduler (rejected: in-process only, won't scale).

---

## CONSTRAINT-010 — Authentication Architecture

type: api-contract
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (sections 2.9, 7)

Two distinct auth domains:
1. App auth — self-hosted JWT with python-jose + Argon2 password hashing. Email/password or Google OAuth. No hosted auth vendor.
2. Host-platform auth — per-platform OAuth tokens (Yahoo, ESPN, etc.) stored encrypted in oauth_credentials.

Session strategy:
- Access tokens: 15-minute JWT, HS256, Authorization: Bearer header
- Refresh tokens: 30-day rotating opaque tokens, hashed in sessions table, httpOnly; Secure; SameSite=Lax cookies
- Sliding session: any refresh extends the 30-day window

Credential storage:
- Master key: MASTER_ENCRYPTION_KEY env var, 256-bit, never logged
- Per-user envelope key, wrapped with master key
- Refresh tokens encrypted with per-user envelope key
- Access tokens short-lived; refreshed just-in-time; cached for documented lifetime minus 60 seconds
- Refresh token rotation on each use

---

## CONSTRAINT-011 — Hosting

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 2.10)

MVP: Single Digital Ocean droplet (Postgres, Redis, app on same box). Pattern matches MonetizedHRD existing infrastructure. V1 target: move Postgres and Redis to managed services when traffic justifies; split app + worker when async load demands it. PM2 for Node process management; systemd unit for Python app. Alternatives evaluated: Render (rejected: more expensive at scale, less control), AWS ECS/Lightsail (rejected: operationally heavy for 2-person team).

Budget constraint: indie scale, no cloud expansion exceeding ~$50/month at MVP.

---

## CONSTRAINT-012 — Mobile and Responsive Strategy

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 8)

Single React codebase with breakpoint-driven layouts. No separate mobile app in V1 (PWA only). Three breakpoints: phone (< 640px), tablet (640–1024px), desktop (> 1024px). Touch-first interactions for swap/reorder UX (drag-and-drop must use pointer events, not just mouse). Service worker for offline reads of cached state (V1). PWA install prompt after first successful league connection. Native apps deferred indefinitely.

---

## CONSTRAINT-013 — Real-Time Performance Budget

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 1)

- Pick propagation: sub-500ms p99 for all draft room participants
- Snappy non-draft UX: most reads must come from cache
- Write endpoints: rate limited at 10 req/sec burst, 100 req/min sustained per user

---

## CONSTRAINT-014 — Security Baseline

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 10)

MVP-level commitments:
- All credentials encrypted at rest with documented key management
- TLS everywhere; HSTS preload after V1 stabilizes
- Input validation via Pydantic on every endpoint
- CSRF protection on cookie-bearing endpoints; SameSite=Lax as second line
- Audit log table for sensitive actions (credential add/remove, password change, league disconnect)
- Rate limiting per user on all write endpoints
- Dependency scanning via pip-audit and npm audit in CI; high-severity findings fail the build

Full security review before V1 ships.

---

## CONSTRAINT-015 — Observability

type: nfr
source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 9)

- Logs: structured JSON to stdout; journald on droplet; rotate after 7 days; Sentry for errors
- Metrics: Prometheus-style endpoint scraped by Grafana Cloud free tier; key dashboards for request latency, cache hit rate, upstream platform errors, draft-room latency p99
- Tracing: deferred; Sentry performance view sufficient at current scale
- Alerting: Discord webhook for warning/critical events (no PagerDuty)

---

## Open Architecture Questions (Unresolved)

source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 11)

These are flagged as needing design-vote issues. They are not constraints yet but become blockers if not resolved before the relevant phase begins:

1. LLM provider for trade analysis: Claude (Anthropic) vs GPT-4o (OpenAI). Must resolve before Phase 7.
2. Hosted Postgres vs droplet Postgres for MVP. Must resolve before Phase 0 deploy.
3. Sleeper as the "demo without auth" path for marketing. Must resolve before Phase 1.
4. CLI for power users. Low priority; can remain open.
5. Public read-only league pages. V2 consideration; adds auth and privacy surface.
