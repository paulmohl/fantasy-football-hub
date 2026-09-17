# CLAUDE.md — Fantasy Football Hub

See `~/.claude/CLAUDE.md` for the global config (identity, rules, preferences, context file map).

---

## Project Overview

Fantasy Football Hub is a serious multi-platform fantasy football companion for competitive leagues. It connects to Sleeper, Yahoo, and ESPN leagues and provides lineup optimization, a live draft room with chat and optional video, and a trade evaluator with AI-powered analysis.

**GitHub:** https://github.com/paulmohl/fantasy-football-hub
**Live mockups:** https://paulmohl.github.io/fantasy-football-hub/mockups/

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend language | Python 3.11 + FastAPI (async) |
| ORM / migrations | SQLAlchemy 2 (async) + Alembic |
| Real-time | python-socketio + Redis adapter (namespaces: `/draft`, `/league`) |
| Background jobs | arq (asyncio-native, Redis-backed) |
| Auth | Self-hosted JWT (PyJWT + passlib/bcrypt); 15-min access + 30-day rotating refresh |
| Cache | Redis 7 (TTL cache, pub/sub fan-out, rate-limit counters, Redis Streams for replay) |
| Database | PostgreSQL 16 (JSONB for scoring rules, roster snapshots) |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| UI primitives | Radix UI (copy-in, not a dep) + Lucide React icons |
| State | Zustand (auth, draft, league stores) + TanStack React Query (server state) |
| HTTP client | axios with auto-refresh interceptor (`frontend/src/lib/api.ts`) |
| Socket client | socket.io-client (`frontend/src/lib/socket.ts`) |
| Drag-and-drop | @dnd-kit/core + @dnd-kit/sortable (lineup card) |
| Charts | recharts (trend chart, projection overlays) |
| E2E tests | Playwright (`e2e/`) |
| Backend tests | pytest + pytest-asyncio + pytest-cov + pytest-mock |
| Lint / type check | ruff (Python), mypy (Python), ESLint + TypeScript (frontend) |
| Build system | Hatchling (backend), Vite 5 (frontend) |
| Video/audio | Daily.co managed WebRTC (Phase 6, not yet built) |
| Encryption | Fernet (per-user envelope key for stored OAuth credentials) |
| Email | fastapi-mail + SMTP |
| Error tracking | Sentry (optional, via `SENTRY_DSN`) |

---

## Architecture

```
monorepo/
├── backend/          # FastAPI app + arq worker
│   ├── app/
│   │   ├── main.py           # App factory, Socket.IO setup, CORS, startup/shutdown
│   │   ├── api/v1/           # All HTTP routers (prefix /v1)
│   │   ├── core/             # Config, database, Redis, cache helpers, deps, security
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic (no HTTP concerns)
│   │   ├── sockets/          # Socket.IO namespaces
│   │   ├── data/             # Static data (stadiums, player cross-map seed)
│   │   └── workers/          # arq background task worker
│   ├── alembic/              # DB migration scripts
│   └── tests/                # pytest test suite
├── frontend/
│   └── src/
│       ├── pages/            # LoginPage, ConnectPage, TeamPage, DraftPage, TradePage
│       ├── components/       # Shared UI + draft/ subfolder for draft room
│       ├── store/            # Zustand stores: auth.ts, draft.ts, league.ts
│       ├── lib/              # api.ts (axios), socket.ts, utils.ts
│       └── plugins/          # espn-cookie Capacitor plugin
├── e2e/                      # Playwright E2E tests + fixtures
├── mockups/                  # Static HTML mockups (hosted on GitHub Pages)
└── .planning/                # GSD planning docs (PROJECT.md, ROADMAP.md, STATE.md, phases/)
```

### Critical routing note — DO App Platform path stripping

Digital Ocean App Platform strips the `/api` prefix from incoming requests before forwarding to the backend container. **The backend router prefix is `/v1` (not `/api/v1`)**. Tests and the frontend must use `/v1/...` paths, not `/api/v1/...`.

- Frontend API calls → `https://<app>/api/v1/...` (DO strips `/api`, backend sees `/v1/...`)
- Socket.IO is mounted at `/ws` (DO forwards `/ws` requests directly to backend)

### Socket.IO design

- `sio` (AsyncServer) is instantiated in `main.py` with Redis adapter for multi-instance fan-out
- `/draft` namespace: `DraftNamespace` class in `app/sockets/draft_namespace.py` — handles all draft room events (make_pick, resume_from, reactions, chat, etc.)
- `/league` namespace: planned for trade pings, lineup alerts, injury alerts
- Draft writes are serialized via a Redis lock keyed `draft:{id}:lock`
- Missed events replayed from Redis Streams (`stream:draft:{id}`, exclusive lower bound on XRANGE)
- Combined ASGI app: `combined_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws")`

---

## Key Files

### Backend

| File | Purpose |
|------|---------|
| `backend/app/main.py` | App factory, Socket.IO setup, CORS, session middleware, startup/shutdown |
| `backend/app/api/v1/__init__.py` | Top-level router (prefix `/v1`); imports all sub-routers |
| `backend/app/core/config.py` | pydantic-settings `Settings` class; all env vars |
| `backend/app/core/deps.py` | FastAPI dependency injection: `get_current_user`, `get_league_for_user` |
| `backend/app/core/cache.py` | `CacheKey` enum, `CacheTTL` constants, cache stampede helpers |
| `backend/app/core/rate_limit.py` | `check_platform_rate_limit` dep; `RateLimitedWithCache` exception (returns cached data with X-Rate-Limited header) |
| `backend/app/core/redis.py` | Shared async Redis client (get/close) |
| `backend/app/core/security.py` | JWT encode/decode, password hashing (bcrypt), Fernet envelope encryption |
| `backend/app/models/user.py` | `User`, `Session` ORM models |
| `backend/app/models/league.py` | `League`, `LeagueMember`, `Team`, `Roster` ORM models |
| `backend/app/models/credential.py` | `UserCredential`, `PlayerCrossMap` ORM models |
| `backend/app/models/draft.py` | `Draft`, `DraftPick` ORM models |
| `backend/app/models/player.py` | `Player` ORM model |
| `backend/app/models/audit.py` | `AuditLog` ORM model |
| `backend/app/services/auth_service.py` | Register, login, token refresh, password reset, Google OAuth |
| `backend/app/services/credential_service.py` | Fernet encrypt/decrypt/store/rotate per user+platform |
| `backend/app/services/sleeper_client.py` | Sleeper REST API HTTP wrapper (no OAuth) |
| `backend/app/services/yahoo_client.py` | Yahoo Fantasy API — OAuth flow, token refresh |
| `backend/app/services/espn_client.py` | ESPN cookie-based private auth + unauthenticated public |
| `backend/app/services/league_service.py` | import_league, refresh_league, classify_draft (unified across platforms) |
| `backend/app/services/yahoo_service.py` | Yahoo → unified League/Team/Roster models |
| `backend/app/services/espn_service.py` | ESPN → unified League/Team/Roster models |
| `backend/app/services/projection_service.py` | FantasyCalc + Sleeper projection merge |
| `backend/app/services/weather_service.py` | Open-Meteo API + indoor stadium exclusion |
| `backend/app/services/lineup_optimizer.py` | `LineupOptimizer` class — greedy slot assignment, confidence scores, OUT replacement |
| `backend/app/services/waiver_ranker.py` | Dual-mode waiver scoring (trend + composite) |
| `backend/app/services/trade_evaluator.py` | Head-to-head comparison (Phase 2 stub; full evaluator Phase 7) |
| `backend/app/services/player_id_mapper.py` | Cross-platform player ID mapping (ffb_ids CSV seed + fuzzy fallback) |
| `backend/app/services/draft_service.py` | Draft creation, pick processing, auto-draft, recap, ADP grading |
| `backend/app/sockets/draft_namespace.py` | Socket.IO DraftNamespace — all real-time draft events |
| `backend/app/data/nfl_stadiums.py` | 32 NFL stadiums with `indoor` flag (SoFi treated as indoor=True) |
| `backend/app/data/player_cross_map_seed.py` | Static player ID cross-map seed data |
| `backend/workers/tasks.py` | arq `WorkerSettings` — scheduled background tasks (league sync, health checks, purge) |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/App.tsx` | React Router setup, page routes, auth guards |
| `frontend/src/lib/api.ts` | axios instance with JWT refresh interceptor |
| `frontend/src/lib/socket.ts` | Socket.IO client factory |
| `frontend/src/store/auth.ts` | Zustand auth store (userId, token, hasLeagues) |
| `frontend/src/store/league.ts` | Zustand league store (active league, switcher) |
| `frontend/src/store/draft.ts` | Zustand draft store (board state, pick queue, chat) |
| `frontend/src/pages/LoginPage.tsx` | Email/password + Google OAuth login |
| `frontend/src/pages/ConnectPage.tsx` | Dual-mode: 5-step conversational onboarding + My Connections list |
| `frontend/src/pages/TeamPage.tsx` | Team Manager — lineup, waiver wire, standings, player detail |
| `frontend/src/pages/DraftPage.tsx` | Bloomberg Terminal draft room shell |
| `frontend/src/pages/TradePage.tsx` | Trade builder (stub — Phase 7) |
| `frontend/src/components/draft/DraftRoom.tsx` | Main draft room layout orchestrator |
| `frontend/src/components/draft/DraftBoard.tsx` | Pick board grid (snake layout, round × slot) |
| `frontend/src/components/draft/PickClock.tsx` | Countdown clock with pause/resume |
| `frontend/src/components/draft/BestAvailable.tsx` | Searchable best available player list |
| `frontend/src/components/draft/RosterPanel.tsx` | Current team roster view (grouped by round) |
| `frontend/src/components/draft/PreDraftLobby.tsx` | Pre-draft lobby with draft order display |
| `frontend/src/components/draft/DraftRecap.tsx` | Post-draft recap with team grades, value picks |
| `frontend/src/components/Layout.tsx` | App shell — bottom tab bar (mobile) + top rail (desktop) |
| `frontend/src/components/HealthBanner.tsx` | Banner shown when platform credentials have expired |

---

## How to Run Locally

### Option 1 — Docker Compose (recommended, all services)

```bash
cp .env.example .env
# Fill in JWT_SECRET and APP_SECRET_KEY (32+ chars each)
docker compose up
```

Services started:
- `postgres` → localhost:5432 (db: ffhub, user: ffhub, pass: ffhub)
- `redis` → localhost:6379
- `backend` → http://localhost:8000 (uvicorn --reload)
- `worker` → arq worker (background jobs)
- `frontend` → http://localhost:5173 (Vite dev server)

### Option 2 — Run services separately

```bash
# 1. Start infrastructure
docker compose up postgres redis

# 2. Backend
cd backend
pip install ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. arq worker (separate terminal)
cd backend
arq workers.tasks.WorkerSettings

# 4. Frontend
cd frontend
npm install
npm run dev
```

### Running tests

```bash
# Backend unit + integration tests
cd backend
pytest --tb=short -q

# Backend lint + type-check
ruff check app workers
mypy app --ignore-missing-imports

# Frontend
cd frontend
npm run type-check
npm run lint
npm run build

# E2E (Playwright)
cd e2e
npm install
npx playwright test
```

---

## Environment Variables

Copy `.env.example` to `.env`. The backend reads these via `app/core/config.py` (pydantic-settings).

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://ffhub:ffhub@localhost:5432/ffhub` |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` |
| `JWT_SECRET` | Yes | 32+ char random string for JWT signing |
| `APP_SECRET_KEY` | Yes | 32+ char random string for Starlette session middleware |
| `JWT_EXPIRE_MINUTES` | Yes | Access token lifetime (default: 15) |
| `IS_PRODUCTION` | Yes | `false` locally; `true` disables /docs |
| `SLEEPER_API_BASE` | Yes | `https://api.sleeper.app/v1` |
| `GOOGLE_CLIENT_ID` | No | For Google OAuth sign-in |
| `GOOGLE_CLIENT_SECRET` | No | For Google OAuth sign-in |
| `GOOGLE_REDIRECT_URI` | No | `http://localhost:8000/v1/auth/google/callback` |
| `MAIL_SERVER` | No | SMTP host (default: smtp.gmail.com) |
| `MAIL_PORT` | No | SMTP port (default: 587) |
| `MAIL_USERNAME` | No | SMTP username |
| `MAIL_PASSWORD` | No | SMTP password |
| `MAIL_FROM` | No | Sender address |
| `MAIL_TLS` | No | `true` / `false` |
| `YAHOO_CLIENT_ID` | No | For Yahoo OAuth connector (Phase 3) |
| `YAHOO_CLIENT_SECRET` | No | For Yahoo OAuth connector (Phase 3) |
| `SENTRY_DSN` | No | Sentry error tracking DSN |
| `FRONTEND_URL` | No | CORS origin for Socket.IO (default: http://localhost:5173) |

---

## Current State

**As of July 4, 2026** (see `.planning/STATE.md` for live state):

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Project Setup | **Complete** (2026-06-22) |
| 1 | League Connector MVP | **In progress** — backend auth, Sleeper client, league routes, frontend auth flow and ConnectPage implemented |
| 2 | Team Manager Core | **Backend complete** through plan 02-12 (ProjectionService, WeatherService, LineupOptimizer, WaiverRanker, TradeEvaluator, all routes, all frontend components) |
| 3 | Multi-Platform Connectors (Yahoo + ESPN) | **Plans written**, partial implementation — plan files modified in current git status |
| 4 | Live Draft Room (Snake) | **Backend + frontend complete** through plan 04-13 (DraftNamespace, board, pick clock, BestAvailable, RosterPanel, QueuePanel, ChatPanel, AlertsPanel, DraftRecap, in-app notifications) |
| 5 | Auction Draft Variant | Not started |
| 6 | Video/Audio (Daily.co) | Not started |
| 7 | Trade Finder & Evaluator | Not started (stub endpoints exist) |
| 8 | Polish, Mobile, PWA | Not started |

**Hard deadline:** Draft Room (Phase 4) before end of August 2026 — Phase 4 backend/frontend is done; Phase 5/6 may also need to complete before that deadline.

---

## Known Issues / Decisions Pending

- **Hosted vs droplet Postgres**: Open architecture question. Currently running on a single DO droplet. Must resolve before Phase 0 deploy is considered stable.
- **LLM provider for trade AI**: Provisionally Claude API; must vote before Phase 7 implementation.
- **Audio placeholders**: `backend/app/public/sounds/` contains 44-byte placeholder MPEG frames — must replace with CC0 audio from freesound.org before E2E tests run against sound cues.
- **Sleeper anonymous demo path**: Decision pending on whether to expose a read-only Sleeper view without login (marketing/onboarding hook).
- **Draft Room phases 5 + 6**: Auction variant and Daily.co video are not started; if the August 2026 hard deadline means the full draft experience, these need to start immediately.

---

## Development Notes and Gotchas

- **Route prefix**: Backend router is `/v1` (DO strips `/api`). Every test, curl, and frontend API call uses `/v1/...`. The historical commit messages explain the fix in detail.
- **Auth store field name**: `useAuthStore(s => s.userId)` — it's `userId` (camelCase), not `user_id`. Using `s.user_id` always returns undefined.
- **Toast API**: `toast(message, variant)` — not `addToast({...})`.
- **Bench slots**: Labeled `'BN'` (not `'BN1'`/`'BN2'`). The optimizer filters with `slot not in ('BN', 'IR')`.
- **FantasyCalc endpoint**: Use `/values/current` (not `/values?sport=nfl` which returns 404).
- **SoFi Stadium**: Treated as `indoor=True` (weather-controlled despite transparent roof).
- **build_sleeper_id_index**: Pure dict comprehension — synchronous, no I/O.
- **XRANGE replay**: Uses exclusive lower bound `f'({last_event_id}'` to prevent re-delivering the boundary event on reconnect (DR-15).
- **DraftPick constraints**: Named `uq_draft_picks_draft_pick_num` and `uq_draft_picks_draft_player` for threat model enforcement at DB level.
- **Migration 003**: Uses `sa.JSON()` (not `JSONB`) for SQLite test compatibility; models use `JSONB` for production Postgres indexing.
- **Route ordering**: `/league/{league_id}` registered before `/{draft_id}` to prevent Starlette matching the literal string `'league'` as a UUID draft_id.
- **Capacitor**: `frontend/capacitor.config.ts` and `@capacitor/*` deps are present for future native app wrapping — not currently used.

---

## CI / CD

- **CI**: GitHub Actions (`.github/workflows/ci.yml`) on push to `master` and all PRs.
  - Backend job: ruff → mypy → pytest (with real Postgres + Redis services)
  - Frontend job: type-check → lint → build
- **Deploy**: Digital Ocean App Platform (`.do/app.yaml`). `deploy_on_push: false` — deployments are manual triggers.
  - Backend: Dockerfile in `backend/`, runs uvicorn
  - Worker: same Dockerfile, runs `arq workers.tasks.WorkerSettings`
  - Frontend: static site build with `npm ci && npm run build`, output `dist/`
  - Post-deploy job: runs `alembic upgrade head` automatically
- **Dependabot**: `.github/dependabot.yml` configured (ecosystem TBD in that file).

---

## Roadmap Summary

See `.planning/ROADMAP.md` for full detail. Execution order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.

The four product pillars:
1. **League Connector** — Connect Sleeper (no OAuth), Yahoo (OAuth), ESPN (cookie-based)
2. **Team Manager** — Lineup optimizer, waiver wire, start/sit recommendations with weather and injury context
3. **Draft Room** — Bloomberg Terminal aesthetic, real-time snake/auction draft, chat, optional video
4. **Trade Evaluator** — Decision-tree impact analysis, multi-lens value, AI natural-language summary
