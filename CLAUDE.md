# CLAUDE.md — Fantasy Football Hub

See `~/.claude/CLAUDE.md` for the global config (identity, rules, preferences, context file map).

---

## Project Overview

Fantasy Football Hub is a serious multi-platform fantasy football companion for competitive leagues. It connects to Sleeper, Yahoo, and ESPN leagues and provides lineup optimization, a live draft room with chat and optional video, and a trade evaluator with AI-powered analysis.

**GitHub:** https://github.com/paulmohl/fantasy-football-hub
**Live mockups:** https://paulmohl.github.io/fantasy-football-hub/mockups/
**Hard deadline:** Draft Room (Phase 4) before end of August 2026 — **already complete as of July 2026**

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend language | Python 3.11+ / FastAPI (async-native) |
| ORM / migrations | SQLAlchemy 2 (async) + Alembic |
| Real-time | python-socketio + Redis adapter (`/draft` and `/league` namespaces) |
| Background jobs | arq (asyncio-native, Redis-backed) |
| Auth | Self-hosted JWT (PyJWT + passlib/bcrypt); 15-min access + 30-day rotating refresh |
| OAuth credentials | Fernet encryption (per-user envelope key wrapping stored platform tokens) |
| Cache | Redis 7 (TTL cache, pub/sub fan-out, rate-limit counters, Redis Streams for event replay) |
| Database | PostgreSQL 16 (JSONB for scoring rules and roster snapshots) |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| UI primitives | Radix UI (copy-in shadcn pattern) + Lucide React icons |
| State | Zustand (auth, draft, league stores) + TanStack React Query (server state) |
| HTTP client | axios with auto-refresh interceptor (`frontend/src/lib/api.ts`) |
| Socket client | socket.io-client (`frontend/src/lib/socket.ts`) |
| Drag-and-drop | @dnd-kit/core + @dnd-kit/sortable |
| Charts | recharts v3 |
| E2E tests | Playwright (`e2e/`) — 49-50 specs passing |
| Backend tests | pytest + pytest-asyncio + pytest-cov + pytest-mock — 150 passing |
| Lint / type check | ruff + mypy (Python), ESLint + TypeScript compiler (frontend) |
| Build system | Hatchling (backend), Vite 5 (frontend) |
| Video/audio | Daily.co managed WebRTC (Phase 6 — not yet built) |
| Email | fastapi-mail + SMTP |
| Error tracking | Sentry (optional, `SENTRY_DSN`) |
| Native wrapper | Capacitor 8 (stubs present; not yet activated) |

---

## Architecture

```
monorepo/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI + Socket.IO setup, CORS, session middleware
│   │   ├── api/v1/             # All HTTP routers (prefix /v1)
│   │   │   ├── auth.py         # email/password + Google OAuth
│   │   │   ├── oauth.py        # Yahoo OAuth flow (authlib)
│   │   │   ├── users.py        # /users/me with credential_health
│   │   │   ├── sleeper.py      # /sleeper/lookup, /sleeper/import
│   │   │   ├── yahoo.py        # /yahoo/leagues, /yahoo/import
│   │   │   ├── espn.py         # /espn/connect (private), /espn/public
│   │   │   ├── leagues.py      # league CRUD and management
│   │   │   ├── team.py         # /team/my, /lineup, /waiver, /standings, /trade
│   │   │   ├── draft.py        # all draft routes + background helpers
│   │   │   ├── notifications.py# GET /notifications (read-once Redis list)
│   │   │   └── health.py       # GET /v1/health
│   │   ├── core/
│   │   │   ├── config.py       # pydantic-settings Settings class
│   │   │   ├── database.py     # async SQLAlchemy engine + session factory
│   │   │   ├── redis.py        # shared async Redis client
│   │   │   ├── cache.py        # CacheKey enum + CacheTTL constants
│   │   │   ├── deps.py         # FastAPI deps: get_current_user, get_league_for_user, get_draft_for_user
│   │   │   ├── security.py     # JWT encode/decode, bcrypt, Fernet encryption
│   │   │   ├── rate_limit.py   # check_platform_rate_limit dep; RateLimitedWithCache exception
│   │   │   └── logging.py      # structlog configuration
│   │   ├── models/
│   │   │   ├── user.py         # User, Session
│   │   │   ├── league.py       # League, LeagueMember, Team, Roster
│   │   │   ├── credential.py   # UserCredential, PlayerCrossMap
│   │   │   ├── draft.py        # Draft, DraftPick, DraftQueue, DraftChatMessage, UserDraftRankings
│   │   │   ├── player.py       # PlayerCrossMap (extended in Phase 3)
│   │   │   └── audit.py        # AuditLog
│   │   ├── services/
│   │   │   ├── auth_service.py         # register, login, token refresh, password reset, Google OAuth
│   │   │   ├── credential_service.py   # Fernet encrypt/decrypt/store/rotate per user+platform
│   │   │   ├── sleeper_client.py       # Sleeper REST API wrapper (no OAuth)
│   │   │   ├── yahoo_client.py         # Yahoo Fantasy API + OAuth token refresh
│   │   │   ├── yahoo_service.py        # Yahoo → unified League/Team/Roster models
│   │   │   ├── espn_client.py          # ESPN cookie-based private + unauthenticated public
│   │   │   ├── espn_service.py         # ESPN → unified League/Team/Roster models
│   │   │   ├── league_service.py       # import_league, refresh_league, classify_draft
│   │   │   ├── projection_service.py   # FantasyCalc + Sleeper projection merge
│   │   │   ├── weather_service.py      # Open-Meteo + indoor stadium exclusion
│   │   │   ├── lineup_optimizer.py     # LineupOptimizer class (greedy slot assignment, confidence)
│   │   │   ├── waiver_ranker.py        # dual-mode waiver scoring (trend + composite)
│   │   │   ├── trade_evaluator.py      # head-to-head comparison stub (full evaluator Phase 7)
│   │   │   ├── player_id_mapper.py     # cross-platform player ID mapping (ffb_ids CSV + fuzzy)
│   │   │   └── draft_service.py        # create_draft, record_pick, auto-draft, replay, ADP grading
│   │   ├── sockets/
│   │   │   └── draft_namespace.py      # Socket.IO DraftNamespace (/draft)
│   │   ├── data/
│   │   │   ├── nfl_stadiums.py         # 32 NFL stadiums with indoor flag
│   │   │   └── player_cross_map_seed.py# ffb_ids CSV URLs + CSV → DB loader
│   │   └── workers/
│   │       └── league_purge.py         # arq task for purging disconnected leagues
│   ├── alembic/versions/
│   │   ├── 001_phase1_auth_league.py   # users, sessions, leagues, league_members, teams, rosters, audit_log
│   │   ├── 002_phase3_credentials_playermap.py  # user_credentials, player_cross_map
│   │   └── 003_draft_models.py         # drafts, draft_picks, draft_queue, draft_chat_messages, user_draft_rankings
│   └── tests/                          # pytest suite (150 tests)
├── frontend/src/
│   ├── App.tsx                 # React Router, RequireAuth (fetches /notifications on mount)
│   ├── pages/
│   │   ├── LoginPage.tsx       # email/password + Google OAuth
│   │   ├── ConnectPage.tsx     # dual-mode: 5-step conversational onboarding + My Connections
│   │   ├── TeamPage.tsx        # Team Manager: lineup, waiver, standings, player detail
│   │   ├── DraftPage.tsx       # Draft room shell: PreDraftLobby / DraftRoom / DraftRecap
│   │   └── TradePage.tsx       # Trade builder stub (Phase 7)
│   ├── components/
│   │   ├── draft/              # All draft room components (16 components)
│   │   └── ui/                 # Shared primitives: Button, Input, Toast, etc.
│   ├── store/
│   │   ├── auth.ts             # userId, token, hasLeagues
│   │   ├── league.ts           # active league, switcher
│   │   └── draft.ts            # board state, picks, queue, chat, available players
│   ├── lib/
│   │   ├── api.ts              # axios with JWT refresh interceptor
│   │   └── socket.ts           # Socket.IO client factory
│   └── plugins/espn-cookie/    # Capacitor plugin for ESPN cookie extraction (native)
├── e2e/tests/                  # Playwright E2E specs (uat-1 through uat-11, 49-50 passing)
├── workers/tasks.py            # arq WorkerSettings + all background task functions
├── mockups/                    # Static HTML mockups (GitHub Pages)
└── .planning/                  # GSD planning: PROJECT.md, ROADMAP.md, STATE.md, phases/
```

### Critical routing note — DO App Platform path stripping

Digital Ocean App Platform strips the `/api` prefix before forwarding to the backend. **The backend router prefix is `/v1`, not `/api/v1`.** All tests, curl commands, and frontend API calls must use `/v1/...` paths.

- Browser → DO App Platform: `https://<app>/api/v1/...`
- DO strips `/api`, backend sees: `/v1/...`
- Socket.IO: DO forwards `/ws` path directly; backend mounts at `/ws`

This is the source of several historical `fix(tests)` commits. Never add the `/api` prefix back to backend routing.

### Socket.IO design

- `sio` (AsyncServer) initialized in `main.py` with Redis adapter for multi-instance fan-out
- `/draft` namespace: `DraftNamespace` in `app/sockets/draft_namespace.py` — handles all draft events
- `/league` namespace: planned (Phase 7) for trade pings, lineup alerts, injury alerts
- Draft writes serialized via Redis lock `draft:{id}:lock`
- Missed events replayed from Redis Streams (`stream:draft:{id}`) — exclusive XRANGE lower bound prevents re-delivery of boundary event on reconnect
- Combined ASGI app: `socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws")`
- `/draft` registered in `main.py` before `ASGIApp` construction (order matters)

### Rate limiting

Redis fixed-window counters per platform per user. When limit is hit, `RateLimitedWithCache` exception is raised — the app-level handler in `main.py` returns the cached response body with `X-Rate-Limited: true` header and HTTP 200 (not 429). Platform 429 exceptions go to the standard 429 handler. The frontend listens for `X-Rate-Limited` and dispatches a `rate-limited` DOM event caught by `RateLimitListener` in App.tsx.

**Conservative limits enforced in Redis:**
- Yahoo: 200 req/user/window
- ESPN: 100 req/user/window

---

## Database Schema

Three Alembic migrations define the full schema:

| Table | Migration | Purpose |
|-------|-----------|---------|
| `users` | 001 | Email, password_hash, display name, verified flag |
| `sessions` | 001 | Rotating refresh tokens (hashed), 30-day sliding window |
| `leagues` | 001 | Deduplicated by `(host_platform, host_league_id, season)`, JSONB scoring_rules/roster_format |
| `league_members` | 001 | Bridge: user ↔ league, role (owner/commissioner/viewer) |
| `teams` | 001 | League team with optional owner_user_id |
| `rosters` | 001 | Per-team per-week snapshot as JSONB |
| `audit_log` | 001 | Sensitive action audit trail |
| `user_credentials` | 002 | Platform OAuth tokens encrypted with per-user Fernet envelope key, `is_healthy` flag |
| `player_cross_map` | 002 | Cross-platform player ID mapping (Sleeper ↔ Yahoo ↔ ESPN) |
| `drafts` | 003 | Snake draft state, pick clock, `draft_order` as JSON array |
| `draft_picks` | 003 | Picks with `reactions` JSONB; named unique constraints at DB level |
| `draft_queue` | 003 | Per-user ranked player queues |
| `draft_chat_messages` | 003 | Draft chat (indexed by draft_id + created_at) |
| `user_draft_rankings` | 003 | Per-user custom ADP rankings (overrides FantasyCalc defaults) |

---

## Key Files Quick Reference

### Backend

| File | What to look for |
|------|-----------------|
| `app/main.py` | App factory, Socket.IO setup, CORS origins, startup/shutdown, `RateLimitedWithCache` handler |
| `app/core/config.py` | All env var names and defaults; `fix_db_scheme` and `fix_redis_scheme` validators |
| `app/core/deps.py` | `get_current_user`, `get_league_for_user`, `get_draft_for_user` — all route protection |
| `app/core/cache.py` | `CacheKey` enum (all Redis key patterns), `CacheTTL` constants, stampede protection helper |
| `app/core/rate_limit.py` | `check_platform_rate_limit(platform)` dep, `RateLimitedWithCache` exception |
| `app/api/v1/draft.py` | 7 routes + `_push_draft_notifications` + `_send_draft_invites`; `GET /{id}/players` returns sorted active players |
| `app/api/v1/notifications.py` | `GET /notifications` — reads + deletes `notifications:{user_id}` Redis list (read-once semantics) |
| `app/api/v1/oauth.py` | Yahoo OAuth registration (`fspt-w` scope); `GET /auth/yahoo`, `GET /auth/yahoo/callback` |
| `app/services/draft_service.py` | `select_auto_draft_player` (queue-first then ADP), `snake_pick_to_slot`, `arm_auto_draft_timer`, `compute_adp_grades`, `record_draft_event`, `replay_since` |
| `app/sockets/draft_namespace.py` | `DraftNamespace` — all Socket.IO `/draft` events (connect, make_pick, add_to_queue, chat, react, pause/resume, reconnect) |
| `workers/tasks.py` | `WorkerSettings` with all arq functions and cron schedule |

### Frontend

| File | What to look for |
|------|-----------------|
| `src/App.tsx` | React Router, `RequireAuth` (fetches `/notifications` on mount, toasts each), `RateLimitListener` |
| `src/lib/api.ts` | axios instance; refresh interceptor; URL pattern check skips refresh for `/espn/`, `/yahoo/`, `/sleeper/` routes |
| `src/store/draft.ts` | `DraftConfig` interface (includes `commissioner_user_id`); `addPick`, `setAvailablePlayers`, `addChatMessage` |
| `src/pages/DraftPage.tsx` | Three-mode render: `pending` → PreDraftLobby, `live/paused` → DraftRoom, `complete` → DraftRecap; fetches players on mount |
| `src/components/draft/DraftRoom.tsx` | 4-column Bloomberg Terminal layout; PauseOverlay + PickDrawer; all 7 panel imports wired |
| `src/components/draft/DraftRecap.tsx` | Grades, value picks, reaches, pick log; `html2canvas` PNG export to `draft-recap.png` |
| `src/components/draft/PickCell.tsx` | `onContextMenu` → `ReactionPicker`; guard `if (!pick) return` on filled cells only |
| `src/components/ui/Toast.tsx` | `toast(message, variant)` API — NOT `addToast({...})` |

---

## How to Run Locally

### Docker Compose (all services, recommended)

```bash
cp .env.example .env
# Set JWT_SECRET and APP_SECRET_KEY to 32+ char random strings
docker compose up
```

All services restart automatically (`restart: unless-stopped` on every container). Services:
- `postgres` → localhost:5432 (db: ffhub, user: ffhub, pass: ffhub)
- `redis` → localhost:6379
- `backend` → http://localhost:8000 (uvicorn --reload, backend volume-mounted)
- `worker` → arq background task runner
- `frontend` → http://localhost:5173 (Vite --reload, src volume-mounted)

### Run separately

```bash
# Infrastructure only
docker compose up postgres redis

# Backend
cd backend
pip install ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# arq worker (separate terminal)
cd backend
arq workers.tasks.WorkerSettings

# Frontend
cd frontend
npm install
npm run dev
```

### Tests

```bash
# Backend
cd backend
pytest --tb=short -q                      # 150 tests
ruff check app workers                    # lint
mypy app --ignore-missing-imports         # type check

# Frontend
cd frontend
npm run type-check
npm run lint
npm run build

# E2E (requires running backend + frontend)
cd e2e
npm install
npx playwright test
```

---

## Environment Variables

All read by `backend/app/core/config.py` via pydantic-settings. Copy `.env.example` to `.env` to start.

| Variable | Required | Default / Notes |
|----------|----------|-----------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://ffhub:ffhub@localhost:5432/ffhub` — scheme auto-fixed from `postgres://` or `postgresql://` |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` |
| `JWT_SECRET` | Yes | 32+ char random string |
| `APP_SECRET_KEY` | Yes | 32+ char random string (Starlette session middleware) |
| `JWT_EXPIRE_MINUTES` | Yes | `15` |
| `IS_PRODUCTION` | Yes | `false` locally; disables `/docs` when `true` |
| `APP_ENV` | No | `development` |
| `APP_BASE_URL` | No | `http://localhost:8000` |
| `FRONTEND_URL` | No | `http://localhost:5173` (CORS origin for Socket.IO) |
| `SLEEPER_API_BASE` | Yes | `https://api.sleeper.app/v1` |
| `GOOGLE_CLIENT_ID` | No | Google OAuth sign-in |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth sign-in |
| `GOOGLE_REDIRECT_URI` | No | `http://localhost:8000/v1/auth/google/callback` |
| `YAHOO_CLIENT_ID` | No* | Yahoo Fantasy API OAuth app — register at developer.yahoo.com |
| `YAHOO_CLIENT_SECRET` | No* | Yahoo Fantasy API OAuth app |
| `ESPN_API_BASE` | No | `https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl` |
| `NFL_SEASON_YEAR` | No | `2025` (used in ESPN routes) |
| `MAIL_SERVER` | No | SMTP host |
| `MAIL_PORT` | No | `587` |
| `MAIL_USERNAME` | No | SMTP username |
| `MAIL_PASSWORD` | No | SMTP password |
| `MAIL_FROM` | No | `noreply@fantasyfootballhub.com` |
| `MAIL_TLS` | No | `true` |
| `SENTRY_DSN` | No | Sentry error tracking |

*`YAHOO_CLIENT_ID`/`YAHOO_CLIENT_SECRET` are optional at startup but required for Yahoo OAuth routes. If absent, `GET /auth/yahoo` returns 503.

---

## Background Jobs (arq)

Run via `arq workers.tasks.WorkerSettings`. All jobs registered in `workers/tasks.py`.

| Job | Schedule | Purpose |
|-----|----------|---------|
| `fantasycalc_prewarm` | Cron: daily 00:05 UTC | Pre-warm FantasyCalc redraft+dynasty values into Redis |
| `seed_player_cross_map` | Cron: Monday 02:00 UTC | Download ffb_ids CSV; bulk-upsert `player_cross_map` |
| `check_platform_credentials` | Cron: every 6h (00:30, 06:30, 12:30, 18:30 UTC) | Validate Yahoo/ESPN tokens; set `is_healthy=False` on auth failure |
| `auto_draft_pick` | On-demand (armed by `arm_auto_draft_timer`) | Auto-draft pick on clock expiry: queue-first then ADP; idempotent via `draft:{id}:current_pick` |
| `post_draft_recap` | On-demand (triggered by final pick) | Compute ADP grades, set `draft.status = complete`, record stream event |

---

## Current State (as of July 2026)

| Phase | Status | What's implemented |
|-------|--------|-------------------|
| **0 — Project Setup** | ✅ Complete | FastAPI scaffold, Socket.IO, Alembic, Redis, Vite/React/Tailwind, CI/CD, DO deploy |
| **1 — League Connector MVP** | ✅ Complete | Email/password auth, Google OAuth, email verification, password reset, Sleeper import, league management, frontend auth flow, ConnectPage (conversational onboarding + My Connections) |
| **2 — Team Manager Core** | ✅ Complete | ProjectionService (FantasyCalc + Sleeper), WeatherService (Open-Meteo + stadiums), LineupOptimizer, WaiverRanker, TradeEvaluator stub, all team routes, all frontend components (LineupCard, WaiverCard, PlayerDetailDrawer, PlayerComparePanel, StandingsCard, TrendChart, AddPlayerDialog, WeatherChip) |
| **3 — Multi-Platform Connectors** | ✅ Complete | CredentialService (Fernet), YahooClient + YahooService, ESPNClient + ESPNService, PlayerCrossMapService (ffb_ids CSV + fuzzy fallback), Yahoo OAuth routes, ESPN connect routes, rate limiting (Redis fixed-window), expired auth detection + HealthBanner, frontend connect flows (Yahoo + ESPN), E2E tests (150 pytest + 49 Playwright) |
| **4 — Live Draft Room (Snake)** | ✅ Complete | DraftNamespace (all Socket.IO events), draft routes (create/schedule/order/pick/queue/chat/react/pause/recap/players/notifications), PreDraftLobby, DraftRoom (Bloomberg Terminal 4-column), DraftBoard, PickClock, BestAvailable, QueuePanel, ChatPanel, AlertsPanel, RosterPanel, PauseOverlay, ReactionPicker, PickDrawer, DraftRecap (grades + html2canvas export), ICS email invites + in-app notifications, auto-draft arq task, Redis Streams reconnect replay — **7/7 roadmap success criteria verified** |
| **5 — Auction Draft Variant** | ⬜ Not started | Nomination, bidding, budget enforcement |
| **6 — Video/Audio (Daily.co)** | ⬜ Not started | Optional video overlay for draft night |
| **7 — Trade Finder & Evaluator** | ⬜ Not started | Decision-tree analysis, AI summary, trade proposals |
| **8 — Polish, Mobile, PWA** | ⬜ Not started | Mobile layouts, PWA, notifications, marketing page |

**Next phase to execute:** Phase 5 (Auction Draft Variant), depends on Phase 4.

---

## Known Issues / Gotchas

### Active bugs / anti-patterns

- **`num_teams=12` hardcoded** in `create_draft` (`draft.py` ~line 94) — non-default league sizes (10, 14 teams) will create a draft with the wrong team count. League model has no `num_teams` field.
- **`team_positions = []`** in `auto_draft_pick` worker (`workers/tasks.py` ~line 296) — positional need weighting in auto-draft is disabled; it always picks best ADP regardless of roster needs.
- **Audio placeholder files** — `frontend/public/sounds/pick.mp3` and `your-turn.mp3` are 44-byte placeholder MPEG frames. Must replace with real CC0 audio from freesound.org before testing audio cues in a live draft.

### Resolved open questions

- **Yahoo Developer App**: must be registered at developer.yahoo.com and `YAHOO_CLIENT_ID`/`YAHOO_CLIENT_SECRET` set in `.env` before Yahoo OAuth routes work. If unset, `/auth/yahoo` returns 503.
- **ESPN public leagues**: do not require cookies. `/espn/public` is read-only (role=viewer); if the league is actually private, returns 403 with instruction to use `/espn/connect`.
- **Yahoo OAuth scope**: `fspt-w` (read+write) is requested at Phase 3 OAuth so users won't need to re-authorize when TM-16 lineup write ships.
- **LLM provider for trade AI**: provisionally Claude API — must vote before Phase 7 implementation.
- **Hosted vs droplet Postgres**: still open but currently running on single DO droplet.

### Development gotchas

- **Route prefix**: always `/v1/...`, never `/api/v1/...`. DO App Platform strips `/api`. Tests must use `/v1/...`.
- **Auth store field**: `useAuthStore(s => s.userId)` — it's `userId` (camelCase). `s.user_id` always returns undefined.
- **Toast API**: `toast(message, variant)` — NOT `addToast({...})`.
- **Bench slot labels**: `'BN'`, not `'BN1'`/`'BN2'`. Optimizer filters `slot not in ('BN', 'IR')`.
- **FantasyCalc endpoint**: `/values/current` (not `/values?sport=nfl` which returns 404).
- **SoFi Stadium**: treated as `indoor=True` (weather-controlled despite transparent roof).
- **Redis Streams replay**: exclusive lower bound `f'({last_event_id}'` on XRANGE prevents re-delivering boundary event on reconnect.
- **DraftPick DB constraints**: named `uq_draft_picks_draft_pick_num` and `uq_draft_picks_draft_player` — enforce uniqueness at DB level per threat model T-4-01.
- **Migration 003 JSON type**: uses `sa.JSON()` not `sa.JSONB()` for SQLite test compatibility; models use `JSONB` for production Postgres indexing.
- **Route ordering**: `/league/{league_id}` route registered before `/{draft_id}` in `draft.py` to prevent Starlette matching the literal string `'league'` as a UUID.
- **`api.ts` 401 interceptor**: skips token refresh for `/espn/`, `/yahoo/`, `/sleeper/` routes to avoid redirecting to login on platform-specific auth failures (e.g., invalid ESPN cookies).
- **`RateLimitListener`**: must be placed outside `<Routes>` in `App.tsx` (non-Route children in React Router v6 are not rendered if inside Routes).
- **`snakePickToSlot` vs `snakeSlot`**: different helpers with different math bases — `snakePickToSlot` maps 1-based pick_num, `snakeSlot` maps 0-based currentPickNum.
- **Database URL**: `config.py` auto-normalizes `postgres://` → `postgresql+asyncpg://` and strips query params (SSL handled by asyncpg defaults).
- **Redis URL**: `config.py` auto-prepends `redis://` if scheme is missing (DO Redis may omit it).

---

## CI / CD

### GitHub Actions (`.github/workflows/ci.yml`)

Runs on push to `master` and all PRs.

- **Backend job**: ruff → mypy → pytest (real Postgres 16 + Redis 7 service containers)
- **Frontend job**: TypeScript type-check → ESLint → Vite build

### Digital Ocean App Platform (`.do/app.yaml`)

`deploy_on_push: false` — deployments are manual. Automatically runs `alembic upgrade head` as a post-deploy job.

| Component | Type | Entry point |
|-----------|------|-------------|
| `backend` | Service | `uvicorn app.main:app --host 0.0.0.0 --port 8000` via Dockerfile |
| `worker` | Worker | `arq workers.tasks.WorkerSettings` via Dockerfile |
| `migrate` | Job (POST_DEPLOY) | `alembic upgrade head` |
| `frontend` | Static site | `npm ci && npm run build` → `dist/` |

Ingress rules: `/api` → backend, `/ws` → backend (all other paths not explicitly handled hit the frontend static site).

---

## Roadmap Summary

See `.planning/ROADMAP.md` for full detail. Execution order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.

**Phases 0–4 complete.** Next: Phase 5 (Auction Draft), then 6 (Video), 7 (Trade Evaluator), 8 (Polish).

The four product pillars:
1. **League Connector** — Sleeper (no OAuth), Yahoo (OAuth `fspt-w`), ESPN (SWID/espn_s2 cookies or public) ✅
2. **Team Manager** — Lineup optimizer, waiver wire, start/sit with weather + injury context ✅
3. **Draft Room** — Bloomberg Terminal aesthetic, real-time snake draft, chat, auto-draft, recap ✅ (Auction variant and Daily.co video next)
4. **Trade Evaluator** — Decision-tree impact analysis, multi-lens value, AI natural-language summary ⬜
