# Phase 1: League Connector MVP — Research

**Researched:** 2026-06-22
**Domain:** FastAPI auth (JWT + Google OAuth), Sleeper public API, SQLAlchemy 2.0 async models, Redis caching, React 18 auth state
**Confidence:** HIGH (most findings verified against live code, official docs, and package registry)

---

## Summary

Phase 1 requires building two orthogonal systems: an auth layer (email/password + Google OAuth + email verification + password reset) and a Sleeper league connector (username lookup → league list → import → persistent cache). Both ship on top of an already-working scaffold (FastAPI app, Socket.IO, Alembic env, React + Tailwind frontend, Zustand auth store, axios client, bottom nav Layout).

The biggest implementation gaps are: (1) no SQLAlchemy models exist yet — `app/models/` is empty; (2) no API routes beyond `/health`; (3) `python-jose` is in `pyproject.toml` but is near-abandoned and incompatible with Python ≥ 3.13 — `PyJWT 2.13.0` is the actively maintained replacement; (4) `passlib` (bcrypt) is scaffolded but maintenance is uncertain beyond Python 3.12 — Argon2 via `argon2-cffi` is the recommended path; (5) Google OAuth requires `authlib` + `itsdangerous` packages not yet in `pyproject.toml`; (6) email delivery (`fastapi-mail`) is not yet installed; (7) the frontend auth store persists the access token to `localStorage` via Zustand `persist` — this conflicts with the architecture decision to use `httpOnly` cookies for refresh tokens; (8) `ConnectPage.tsx` is a step-machine scaffold but calls non-existent backend routes.

The Sleeper API is fully public, requires no auth token, and its endpoints are well-documented. Rate limit is 1000 req/min (IP-level) — far above what any single-user session will consume; the in-app self-imposed limit of 100 req/user/min is still the correct constraint per ARCHITECTURE.md.

**Primary recommendation:** Build models and migrations first (Wave 0), then auth endpoints, then Sleeper service, then the remaining frontend wiring. The UI-SPEC is already complete and pixel-exact — frontend work is mostly replacing the scaffold stubs with real components per the spec.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Email/password signup + verification | API / Backend | — | Token generation, email dispatch, and DB writes all belong server-side |
| Google OAuth redirect + callback | API / Backend | — | Authorization code exchange must happen server-side; tokens never touch client |
| JWT access token (15 min) | API / Backend | Browser / Client | Backend signs; frontend attaches as Bearer header |
| Refresh token (30-day, rotating) | API / Backend | — | Issued as httpOnly cookie; client never reads it directly |
| Email verification token | API / Backend | — | Signed URL token generated and verified server-side via itsdangerous |
| Password reset token | API / Backend | — | Same pattern as email verification token |
| Sleeper username → user_id lookup | API / Backend | Redis | Backend calls Sleeper API; result cached in Redis |
| Sleeper leagues fetch | API / Backend | Redis | Backend fetches; caches league list for session |
| League import (upsert + members) | API / Backend | Postgres | All writes to Postgres; cache set after upsert |
| League settings/roster storage | Database / Storage | Redis | Postgres is truth; Redis serves reads |
| Auth state (is logged in) | Browser / Client | — | Zustand store holds access token; drives `RequireAuth` gate |
| Protected route gating | Browser / Client | — | `RequireAuth` in App.tsx already exists; needs extension for "no leagues" gate |
| Conversational connect UI | Browser / Client | — | React state machine in ConnectPage; calls backend APIs |
| My Connections page | Browser / Client | — | React Query fetches from `/api/v1/leagues/mine`; renders per UI-SPEC |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can sign up with email and password; account created only after email verification | POST `/auth/register` → user created with `is_verified=False`; verification email via fastapi-mail; token via itsdangerous URLSafeTimedSerializer; verify endpoint flips flag |
| AUTH-02 | User can sign in via Google OAuth without entering a password | authlib 1.7.2 + `itsdangerous` + `SessionMiddleware`; `/auth/google` redirect + `/auth/google/callback` exchange; upsert user row on first login |
| AUTH-03 | User can reset a forgotten password via email link | POST `/auth/forgot-password` → generate signed token → send email; POST `/auth/reset-password` → verify token → update hash |
| AUTH-04 | New user with no connections sees "Connect your first league" CTA and cannot reach other features | Backend: GET `/users/me` returns `has_leagues: bool`; Frontend: `RequireLeague` guard in App.tsx disables nav tabs; UI-SPEC Section 5C empty state |
| LC-01 | User can enter a Sleeper username and see a list of their leagues without OAuth | GET `/sleeper/lookup?username=X` → backend calls `GET /user/{username}` then `/user/{user_id}/leagues/nfl/{current_season}` |
| LC-02 | User can select one or more Sleeper leagues to import | POST `/sleeper/import` with `{league_ids: [...]}` → iterates import per ID |
| LC-03 | On import, draft type classified and keeper/dynasty flag set with one-line explanation | Parse `league.settings.draft` from Sleeper API; classify: snake/auction/linear/third_round_reversal; set `keeper_flag` from `league.settings.num_playoff_teams` nesting or dedicated field; store in `leagues.draft_type` |
| LC-04 | Every stat-to-point scoring rule stored in normalized format; non-standard rules flagged | Map `league.scoring_settings` JSONB (as-is from Sleeper); normalized key set identified; flag unknowns |
| LC-05 | Every roster slot captured with its eligibility list; visual roster shape shown | Map `league.roster_positions` array → `leagues.roster_format` JSONB; display deferred to Phase 2 per UI-SPEC Section 13 |
| LC-06 | User sees all their connections grouped by platform with last-sync timestamp and health status | GET `/leagues/mine` → `league_members` JOIN `leagues`; `last_synced_at` from leagues table |
| LC-07 | User can click "Refresh now" to re-pull settings, rosters, matchups within 10 seconds | POST `/leagues/{id}/refresh` → re-calls Sleeper API for league + rosters + users; updates Postgres; invalidates Redis keys |
| LC-08 | Given invalid input, user sees specific human-readable error; no partial connection record | Backend validation: 404 from Sleeper → raise 404 with detail; empty leagues list → 422; import failure → rollback transaction |
| LC-09 | Each user sees only their own connections; accessing another user's league returns 404 | All league endpoints filter by `current_user.id` via dependency; no league ID in URL resolves without ownership check |
| LC-10 | Two users connecting same Sleeper league produce one deduped league record; both see own team highlighted | `leagues` table UNIQUE on `(host_platform, host_league_id, season)`; `league_members` bridges user→league; `teams.owner_user_id` links user to their team |
| LC-11 | User can disconnect a league (credentials deleted, cached data retained 30 days, user confirms) | DELETE `/leagues/{id}/connection` → delete `league_members` row; schedule arq job to purge cached data after 30 days |
| LC-12 | Re-connecting a previously disconnected league is treated as a fresh import | On import, lookup existing `league_members` row; if absent (was deleted), insert fresh; do not restore old `league_members` metadata |
</phase_requirements>

---

## Standard Stack

### Backend — New Packages Needed

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `PyJWT` | 2.13.0 | JWT encode/decode (replace python-jose) | Not in pyproject.toml [VERIFIED: pip registry] |
| `authlib` | 1.7.2 | Google OAuth2 / OpenID Connect client | Not in pyproject.toml [VERIFIED: pip registry] |
| `itsdangerous` | 2.2.0 | Signed URL tokens for email verify + password reset; required by authlib SessionMiddleware | Not in pyproject.toml [VERIFIED: pip registry] |
| `fastapi-mail` | 1.6.5 | Async SMTP email for verification and password reset | Not in pyproject.toml [VERIFIED: pip registry] |
| `argon2-cffi` | 25.1.0 | Argon2 password hashing (replace bcrypt / passlib long-term) | Not in pyproject.toml [VERIFIED: pip registry] |

**Note on python-jose:** Already in `pyproject.toml` (`python-jose[cryptography]>=3.3.0`). It is near-abandoned (last release ~3 years ago) and will break on Python 3.13. `PyJWT 2.x` is the actively maintained replacement recommended by the FastAPI community. [CITED: github.com/fastapi/fastapi/discussions/11345] The scaffold `security.py` uses `jose.jwt` — this must be migrated to `jwt` (PyJWT) in the same task that builds auth models.

**Note on passlib:** In `pyproject.toml` as `passlib[bcrypt]`. Passlib itself is unmaintained (last release 2020) and will break Python 3.13. For Python 3.12 MVP it still works. Keep bcrypt for now via `CryptContext(schemes=["bcrypt"])` — the existing `security.py` uses it. Flag as tech debt; full migration to `argon2-cffi` is a separate future task. [CITED: pypi.org/project/pwdlib/]

### Backend — Already in pyproject.toml (relevant to Phase 1)

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.111.0 | Web framework |
| `httpx` | ≥0.27.0 | Async HTTP client for Sleeper API calls |
| `sqlalchemy` | ≥2.0.0 | Async ORM for models |
| `alembic` | ≥1.13.0 | Migrations — env.py fully configured |
| `pydantic[email]` | ≥2.7.0 | Request/response validation |
| `python-jose[cryptography]` | ≥3.3.0 | JWT (keep until PyJWT migration in same wave) |
| `passlib[bcrypt]` | ≥1.7.4 | Password hashing (use now, migrate later) |
| `redis[hiredis]` | ≥5.0.0 | Cache + rate limiting |
| `arq` | ≥0.26.0 | Background job for 30-day cache purge |
| `structlog` | ≥24.2.0 | Structured logging |

### Frontend — Already in package.json (relevant to Phase 1)

| Library | Version | Purpose |
|---------|---------|---------|
| `@tanstack/react-query` | ^5.45.0 | Server state, cache, loading states |
| `zustand` | ^4.5.2 | Auth state (`useAuthStore` already exists) |
| `axios` | ^1.7.2 | HTTP client (`api.ts` already exists) |
| `react-router-dom` | ^6.23.1 | Routing + `RequireAuth` guard |
| `@radix-ui/react-dialog` | ^1.1.1 | Disconnect confirmation modal |
| `@radix-ui/react-toast` | ^1.2.1 | Toast notifications |
| `@radix-ui/react-checkbox` | (not installed) | League selection checkboxes — needs install |
| `@radix-ui/react-label` | ^2.1.10 | Form labels — available via npm |
| `lucide-react` | ^0.395.0 | Icons |

**Frontend install needed:**
```bash
cd frontend && npm install @radix-ui/react-checkbox @radix-ui/react-label
```
[VERIFIED: npm registry — @radix-ui/react-checkbox@1.3.5, @radix-ui/react-label@2.1.10]

### Backend Installation

```bash
cd backend && pip install "PyJWT>=2.13.0" "authlib>=1.7.2" "itsdangerous>=2.2.0" "fastapi-mail>=1.6.5"
```

Then update `pyproject.toml` to add these and mark `python-jose` for removal in a follow-up.

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (React 18 + Zustand + React Query + Axios)
    |
    | Bearer: access_token (15-min JWT, in-memory)
    | Cookie: refresh_token (30-day, httpOnly, auto-sent)
    |
    v
FastAPI (/api/v1/*)
    |-- /auth/register         POST  → create user (unverified), send email
    |-- /auth/verify-email     GET   → flip is_verified, issue JWT
    |-- /auth/login            POST  → verify password → JWT + set cookie
    |-- /auth/refresh          POST  → rotate refresh token → new JWT
    |-- /auth/logout           POST  → delete refresh token cookie
    |-- /auth/google           GET   → redirect to Google
    |-- /auth/google/callback  GET   → exchange code → upsert user → JWT + cookie
    |-- /auth/forgot-password  POST  → send reset email
    |-- /auth/reset-password   POST  → verify token → update hash
    |-- /users/me              GET   → current user + has_leagues flag
    |-- /sleeper/lookup        GET   → Sleeper API proxy (username → leagues)
    |-- /sleeper/import        POST  → import league(s) into Postgres + cache
    |-- /leagues/mine          GET   → user's connected leagues (from DB)
    |-- /leagues/{id}/refresh  POST  → re-sync from Sleeper API
    |-- /leagues/{id}/connection DELETE → disconnect league
    |
    ├── Sleeper API (api.sleeper.app/v1)   [no auth, read-only]
    ├── PostgreSQL 16                       [source of truth]
    ├── Redis 7                             [cache + rate limit counters]
    ├── SMTP (via fastapi-mail)             [email verification + reset]
    └── Google OAuth (accounts.google.com) [OpenID Connect discovery]
```

### Recommended Project Structure (backend additions)

```
backend/app/
├── models/
│   ├── __init__.py          # import all models so Alembic sees them
│   ├── user.py              # User, Session (refresh tokens)
│   ├── league.py            # League, LeagueMember, Team, Roster
│   └── audit.py             # AuditLog
├── api/v1/
│   ├── __init__.py          # include all routers
│   ├── health.py            # exists
│   ├── auth.py              # email/password + email verify + reset
│   ├── oauth.py             # Google OAuth (authlib)
│   ├── users.py             # /users/me
│   ├── sleeper.py           # /sleeper/lookup + /sleeper/import
│   └── leagues.py           # /leagues/mine + refresh + disconnect
├── services/
│   ├── auth_service.py      # token creation, verification, rotation
│   ├── email_service.py     # fastapi-mail wrapper
│   ├── sleeper_client.py    # httpx calls to Sleeper API
│   └── league_service.py    # import logic, dedup, cache
├── core/
│   ├── security.py          # MIGRATE jose→PyJWT; keep hash_password/verify_password
│   ├── deps.py              # get_current_user dependency
│   └── cache.py             # Redis key helpers + TTL constants
└── workers/
    └── league_purge.py      # arq job: purge 30-day disconnected league cache
```

### Pattern 1: Email/Password Auth with Email Verification

```python
# Source: ARCHITECTURE.md section 7 + CONSTRAINT-010
# security.py — after PyJWT migration
import jwt
from datetime import datetime, timedelta, UTC
from itsdangerous import URLSafeTimedSerializer

def create_access_token(subject: str) -> str:
    payload = {"sub": subject, "exp": datetime.now(UTC) + timedelta(minutes=15)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_email_token(email: str) -> str:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    return s.dumps(email, salt="email-verify")

def verify_email_token(token: str, max_age: int = 86400) -> str | None:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    try:
        return s.loads(token, salt="email-verify", max_age=max_age)
    except Exception:
        return None
```

```python
# deps.py — get_current_user dependency
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
```

### Pattern 2: Refresh Token Cookie Rotation

```python
# Source: ARCHITECTURE.md section 7.3
# On login / token refresh:
def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
        path="/api/v1/auth/refresh",  # scope cookie to refresh endpoint only
    )
```

**CRITICAL:** The current `auth.ts` / `useAuthStore` stores `access_token` in localStorage via Zustand `persist`. This is acceptable for the short-lived access token (15 min). The refresh token MUST be in an httpOnly cookie only, never in localStorage or Zustand state. The `api.ts` interceptor already attaches the Bearer header from the Zustand store — this pattern is fine for the access token.

### Pattern 3: Google OAuth with Authlib

```python
# Source: [CITED: docs.authlib.org/en/stable/client/fastapi.html]
# Requires: authlib>=1.7.2, itsdangerous>=2.2.0, SessionMiddleware in main.py

from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={"scope": "openid email profile"},
)

# In main.py — add before routes:
# app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)

@router.get("/google")
async def google_login(request: Request):
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    # upsert user by google_sub; issue JWT; set refresh cookie
```

**New env vars needed:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (e.g., `http://localhost:8000/api/v1/auth/google/callback`)

### Pattern 4: Sleeper API Client

```python
# Source: [VERIFIED: docs.sleeper.com]
# All endpoints are public, no auth header needed.
# Rate limit: 1000 req/min IP-level (we enforce 100 req/user/min via Redis)

class SleeperClient:
    BASE = "https://api.sleeper.app/v1"

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def get_user(self, username: str) -> dict:
        r = await self.http.get(f"{self.BASE}/user/{username}")
        if r.status_code == 404:
            raise SleeperUserNotFound(username)
        r.raise_for_status()
        return r.json()  # {user_id, username, display_name, avatar}

    async def get_leagues(self, user_id: str, season: str) -> list[dict]:
        r = await self.http.get(f"{self.BASE}/user/{user_id}/leagues/nfl/{season}")
        r.raise_for_status()
        return r.json()  # list of league objects

    async def get_league(self, league_id: str) -> dict:
        r = await self.http.get(f"{self.BASE}/league/{league_id}")
        r.raise_for_status()
        return r.json()  # {league_id, name, status, season, scoring_settings, roster_positions, settings, ...}

    async def get_rosters(self, league_id: str) -> list[dict]:
        r = await self.http.get(f"{self.BASE}/league/{league_id}/rosters")
        r.raise_for_status()
        return r.json()  # [{roster_id, owner_id, starters, players, settings}, ...]

    async def get_users(self, league_id: str) -> list[dict]:
        r = await self.http.get(f"{self.BASE}/league/{league_id}/users")
        r.raise_for_status()
        return r.json()  # [{user_id, username, display_name, avatar, metadata, is_owner}, ...]

    async def get_nfl_state(self) -> dict:
        r = await self.http.get(f"{self.BASE}/state/nfl")
        r.raise_for_status()
        return r.json()  # {week, season, season_type, ...}
```

**Season parameter:** Use `nfl_state.season` (current year string, e.g. `"2025"`) for the leagues lookup. Cache `nfl_state` in Redis with a 1-hour TTL.

**Draft type classification** from `league.settings`:
- `type` field: `"snake"`, `"auction"`, `"linear"`, or `"third_round_reversal"` [CITED: docs.sleeper.com]
- `keeper_flag`: `league.settings.num_keepers > 0` [ASSUMED — exact field name needs verification against live API call]
- `dynasty_flag`: `league.settings.type == "dynasty"` or check `league.league_id` suffix pattern [ASSUMED — Sleeper docs unclear; verify by calling live API]

### Pattern 5: League Import (Dedup + Atomic)

```python
# Source: ARCHITECTURE.md section 3 (data model)
# leagues UNIQUE on (host_platform, host_league_id, season)

async def import_league(league_id: str, current_user: User, db: AsyncSession):
    async with db.begin():  # atomic — rollback on any failure (satisfies LC-08)
        league_data = await sleeper.get_league(league_id)
        rosters = await sleeper.get_rosters(league_id)
        members = await sleeper.get_users(league_id)

        # Upsert league (dedup by host key)
        stmt = pg_insert(League).values(
            host_platform="sleeper",
            host_league_id=league_id,
            season=league_data["season"],
            name=league_data["name"],
            scoring_rules=league_data.get("scoring_settings"),
            roster_format=league_data.get("roster_positions"),
            draft_type=classify_draft(league_data),
            keeper_flag=...,
            last_synced_at=datetime.now(UTC),
        ).on_conflict_do_update(
            index_elements=["host_platform", "host_league_id", "season"],
            set_={"last_synced_at": datetime.now(UTC), "name": league_data["name"]},
        ).returning(League)
        league = (await db.execute(stmt)).scalar_one()

        # Insert league_member for current user (upsert on user_id, league_id)
        # Insert/upsert teams + rosters
        ...

    # After commit: set Redis cache
    await redis.set(f"league:{league.id}:settings", json.dumps(league_data), ex=6*3600)
```

### Pattern 6: Row-Level Ownership Filter (LC-09)

```python
# All league endpoints must filter by current_user — never trust the URL ID alone
# deps.py
async def get_league_for_user(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> League:
    result = await db.execute(
        select(League)
        .join(LeagueMember, LeagueMember.league_id == League.id)
        .where(LeagueMember.user_id == current_user.id)
        .where(League.id == league_id)
    )
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league
```

### Pattern 7: Frontend Auth State + Refresh Flow

The existing `useAuthStore` (Zustand persist) holds `token` and `userId`. The `api.ts` interceptor already attaches Bearer headers and redirects on 401. What's missing:

1. **Refresh token flow:** On 401, before redirecting to `/login`, attempt `POST /api/v1/auth/refresh` (browser sends httpOnly cookie automatically). If it succeeds, retry the original request with the new access token. [CITED: dev.to/elmehdiamlou]
2. **`has_leagues` gate:** After login, call `GET /api/v1/users/me` and check `has_leagues`. Store in Zustand. Use in `RequireLeague` component to disable/enable nav tabs per UI-SPEC Section 6.
3. **Google OAuth redirect:** The Google callback returns a `?token=...` query param or sets a cookie; React catches it and calls `setAuth`. [ASSUMED — specific redirect shape is an implementation decision]

```typescript
// Refresh interceptor addition to api.ts
let isRefreshing = false
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = []

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    if (err.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      originalRequest._retry = true
      isRefreshing = true
      try {
        const { data } = await api.post('/auth/refresh')  // cookie sent automatically
        useAuthStore.getState().setAuth(data.access_token, data.user_id)
        failedQueue.forEach(({ resolve }) => resolve(data.access_token))
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch {
        failedQueue.forEach(({ reject }) => reject(err))
        useAuthStore.getState().clearAuth()
        window.location.href = '/login'
      } finally {
        isRefreshing = false
        failedQueue = []
      }
    }
    return Promise.reject(err)
  }
)
```

### Anti-Patterns to Avoid

- **Hand-rolling Google OAuth PKCE/state validation:** authlib handles state parameter and CSRF cookie automatically — do not implement manually.
- **Storing refresh token in localStorage or Zustand state:** It MUST stay in an httpOnly cookie only.
- **Calling Sleeper API from the browser:** All Sleeper calls go through the backend — rate limiting, caching, and error normalization happen there.
- **Storing jwt_expire_minutes as 7 days (current config.py):** The architecture requires 15-minute access tokens. The config default `jwt_expire_minutes = 60 * 24 * 7` is wrong for the production auth design — fix when building auth.
- **Using `jose.jwt` after migration:** The `security.py` scaffold uses `python-jose`. Once PyJWT is added, all JWT calls must migrate in the same task to avoid dual-library confusion.
- **Trusting URL params for league ownership:** Always join through `league_members` filtered by `current_user.id` — never fetch by league ID alone.
- **Creating a partial `league_members` row on import failure:** The import must be wrapped in a single transaction with rollback on any Sleeper API error (LC-08).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth2 code exchange + state validation | Custom PKCE/state logic | `authlib` AsyncOAuth2Client | State param, token exchange, OpenID discovery, user info fetch — all handled; hand-rolled versions miss CSRF edge cases |
| Signed email verification tokens | UUID in DB with expiry column | `itsdangerous.URLSafeTimedSerializer` | Cryptographic signing, expiry enforcement, and secret rotation without a DB row |
| HTTP client for Sleeper calls | `requests` (sync) | `httpx.AsyncClient` | Async-native; already in pyproject.toml; shares event loop with FastAPI |
| Email sending | Raw smtplib | `fastapi-mail` | Async, template support, BackgroundTask integration, connection pooling |
| Frontend toast system | Custom React component | `@radix-ui/react-toast` | Already in package.json; accessibility (ARIA live region), auto-dismiss, focus management — already handled |
| Frontend modal (disconnect confirm) | Custom `<dialog>` | `@radix-ui/react-dialog` | Already in package.json; focus trap, ESC handling, portal rendering |
| League dedup logic | `INSERT ... IF NOT EXISTS` SELECT pattern | SQLAlchemy `pg_insert(...).on_conflict_do_update()` | Atomic upsert — avoids race condition between two users importing same league simultaneously |
| Cache stampede protection | Sleep-retry loop | Redis SETNX lock + serve-stale per CONSTRAINT-007 | Already specified in architecture — do not re-invent |

**Key insight:** The hardest bugs in this domain come from partial state — a user created without a verification row, a league partially imported, or two users racing to create the same league. Use transactions + atomic upserts everywhere.

---

## Sleeper API — Verified Endpoint Map

[VERIFIED: docs.sleeper.com]

| Step | Endpoint | Response Fields Used |
|------|----------|---------------------|
| Lookup user | `GET /v1/user/{username}` | `user_id`, `username`, `display_name`, `avatar` |
| Get leagues | `GET /v1/user/{user_id}/leagues/nfl/{season}` | `league_id`, `name`, `status`, `total_rosters`, `season`, `avatar` |
| Get league detail | `GET /v1/league/{league_id}` | `league_id`, `name`, `season`, `status`, `scoring_settings` (JSONB), `roster_positions` (array), `settings.draft` / `settings.type`, `draft_id` |
| Get rosters | `GET /v1/league/{league_id}/rosters` | `roster_id`, `owner_id`, `starters`, `players`, `settings.wins`, `settings.losses`, `settings.fpts` |
| Get members | `GET /v1/league/{league_id}/users` | `user_id`, `username`, `display_name`, `avatar`, `metadata.team_name`, `is_owner` |
| NFL state | `GET /v1/state/nfl` | `season` (current year string), `week`, `season_type` |
| Player database | `GET /v1/players/nfl` | ~5 MB blob; all player metadata by player_id — cache 24h; only needed for Phase 2+ |

**Rate limit:** 1000 req/min IP-level (no user-level enforcement from Sleeper). The app enforces its own 100 req/user/min via Redis sliding window per CONSTRAINT-008. [VERIFIED: docs.sleeper.com]

**No auth required for any Sleeper endpoint.** [VERIFIED: docs.sleeper.com]

**Username changes:** Sleeper usernames can change. Always store and use `user_id` for persistent references after initial lookup. [VERIFIED: docs.sleeper.com]

---

## SQLAlchemy Models (Phase 1 Scope)

The current `app/models/` directory is empty. These models are needed for Phase 1 migrations:

```python
# models/user.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str | None]          # None for Google-only accounts
    google_sub: Mapped[str | None] = mapped_column(unique=True)  # Google subject ID
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_login_at: Mapped[datetime | None]
    envelope_key: Mapped[bytes | None]          # per-user envelope key for Phase 3+

class Session(Base):                           # refresh tokens
    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(unique=True)  # SHA-256 of opaque token
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

# models/league.py
class League(Base):
    __tablename__ = "leagues"
    __table_args__ = (
        UniqueConstraint("host_platform", "host_league_id", "season"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    host_platform: Mapped[str]                 # "sleeper"
    host_league_id: Mapped[str]
    season: Mapped[str]
    name: Mapped[str]
    scoring_rules: Mapped[dict] = mapped_column(JSONB)
    roster_format: Mapped[dict] = mapped_column(JSONB)
    draft_type: Mapped[str | None]             # snake / auction / linear / third_round_reversal
    keeper_flag: Mapped[bool] = mapped_column(default=False)
    dynasty_flag: Mapped[bool] = mapped_column(default=False)
    last_synced_at: Mapped[datetime | None]

class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("user_id", "league_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    host_team_id: Mapped[str | None]           # roster_id in Sleeper
    role: Mapped[str] = mapped_column(default="owner")  # owner / commissioner / viewer
    connected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    league_id: Mapped[UUID] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    host_team_id: Mapped[str]                  # roster_id in Sleeper
    name: Mapped[str | None]
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("league_id", "host_team_id"),)

class Roster(Base):
    __tablename__ = "rosters"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    week: Mapped[int] = mapped_column(primary_key=True)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    last_synced_at: Mapped[datetime | None]

# models/audit.py
class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str]                        # "league.connect", "league.disconnect", etc.
    target_type: Mapped[str | None]
    target_id: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    metadata: Mapped[dict | None] = mapped_column(JSONB)
```

**Alembic:** `env.py` is already configured — `import app.models` in `env.py` registers models. After writing models, run `alembic revision --autogenerate -m "phase1_auth_league"`.

---

## Redis Cache Keys (Phase 1 Scope)

[VERIFIED: ARCHITECTURE.md section 5 / CONSTRAINT-007]

| Key | TTL | Set When | Invalidated When |
|----|-----|---------|-----------------|
| `sleeper:user:{username}` | 5 min | Username lookup | Never (short TTL enough) |
| `sleeper:leagues:{user_id}:{season}` | 10 min | leagues list fetch | Manual refresh |
| `league:{id}:settings` | 6 hours | Import or refresh | Manual refresh |
| `league:{id}:rosters:{week}` | 30 min | Import or refresh | Manual refresh |
| `league:{id}:members` | 6 hours | Import or refresh | Manual refresh |
| `nfl:state` | 1 hour | Any call needing current season | TTL-only |
| `ratelimit:sleeper:{user_id}` | sliding 60s | Every Sleeper API call | Sliding window |

---

## What Already Exists (Scaffold Inventory)

**DO NOT re-implement these:**

| Item | File | State |
|------|------|-------|
| FastAPI app + CORS + Socket.IO | `backend/app/main.py` | Complete |
| Settings (pydantic-settings) | `backend/app/core/config.py` | Complete — needs new vars added |
| Async SQLAlchemy engine + session | `backend/app/core/database.py` | Complete |
| Redis client | `backend/app/core/redis.py` | Complete |
| Structlog logging | `backend/app/core/logging.py` | Complete |
| bcrypt hash/verify + JWT sign/decode | `backend/app/core/security.py` | Exists — JWT must migrate from python-jose to PyJWT |
| Alembic env.py (async) | `backend/alembic/env.py` | Complete — reads `app.models` |
| React router + `RequireAuth` guard | `frontend/src/App.tsx` | Complete |
| Zustand auth store (token + userId) | `frontend/src/store/auth.ts` | Complete — needs `has_leagues` field |
| Axios client + Bearer interceptor + 401 redirect | `frontend/src/lib/api.ts` | Complete — needs refresh retry logic |
| Bottom nav Layout with 5 tabs | `frontend/src/components/Layout.tsx` | Complete — needs disabled state for pre-league tabs |
| LoginPage (email+password form) | `frontend/src/pages/LoginPage.tsx` | Scaffold — needs: Google button, forgot password, email verification post-register state |
| ConnectPage (step machine) | `frontend/src/pages/ConnectPage.tsx` | Scaffold — needs: conversational chat UI per UI-SPEC, multi-select leagues, My Connections view |
| Tailwind tokens (colors, fonts) | `frontend/tailwind.config.ts` | Complete per UI-SPEC Section 2 |

**Config gap:** `config.py` has `jwt_expire_minutes = 60 * 24 * 7` (7 days) but the architecture requires 15-min access tokens + 30-day refresh tokens. Fix this in the models/auth task.

---

## Common Pitfalls

### Pitfall 1: Partial Import State on Sleeper API Error
**What goes wrong:** Sleeper's `get_rosters` call succeeds but `get_users` returns a 5xx. Half the import is written to Postgres.
**Why it happens:** Multiple async API calls before a single DB write, no transaction boundary.
**How to avoid:** Collect all Sleeper API responses first (all awaited outside the DB transaction), then open `async with db.begin()` for all DB writes. If any API call fails, the transaction never opens.
**Warning signs:** `league_members` rows without corresponding `teams` rows.

### Pitfall 2: python-jose / PyJWT Dual Library Confusion
**What goes wrong:** New code uses `PyJWT` (`jwt.encode`), but `security.py` still imports `from jose import jwt`. Both libraries have the same top-level function names but different exception classes and payload formats.
**Why it happens:** Incremental migration without a clear cutover task.
**How to avoid:** Migrate `security.py` completely in the same task that adds PyJWT to `pyproject.toml`. Remove `python-jose` in the same commit.

### Pitfall 3: Zustand Auth Store Persisting Refresh Tokens
**What goes wrong:** Dev adds refresh token to `useAuthStore` alongside access token — it gets persisted to `localStorage`.
**Why it happens:** It's the path of least resistance when the refresh endpoint returns both tokens.
**How to avoid:** The `/auth/refresh` endpoint only returns a new `access_token` in the JSON body and sets the refresh token as a cookie. The frontend never receives the raw refresh token value.

### Pitfall 4: Sleeper Season Hardcoded
**What goes wrong:** Season is hardcoded as `"2025"` in the leagues lookup URL. During the off-season transition (early 2026), leagues from 2025 are not found.
**Why it happens:** Easy shortcut during development.
**How to avoid:** Always call `GET /v1/state/nfl` first to get `season` string. Cache this in Redis with 1h TTL.

### Pitfall 5: Google OAuth Callback CSRF Without SessionMiddleware
**What goes wrong:** Without `SessionMiddleware` in FastAPI, `authlib` cannot store the OAuth `state` parameter between the redirect and the callback. The flow fails silently or raises a cryptic error.
**Why it happens:** `SessionMiddleware` requires `itsdangerous` and a secret key — easy to miss.
**How to avoid:** Add `app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)` in `main.py` in the same task as the Google OAuth routes. Both `authlib` and `itsdangerous` must be in `pyproject.toml`.

### Pitfall 6: Sleeper Username Case Sensitivity
**What goes wrong:** User enters `PaulMohl` but Sleeper stores `paulmohl`. The lookup fails with a false 404.
**Why it happens:** Sleeper usernames are case-insensitive at their end but the URL is case-sensitive.
**How to avoid:** `.strip().lower()` the username before passing to the API. [ASSUMED — behavior not explicitly documented; verify during implementation]

### Pitfall 7: ConnectPage vs My Connections — Same Route
**What goes wrong:** `ConnectPage.tsx` currently renders the step machine (onboarding flow). After a league is connected, the same page should render the My Connections view. These are two different UI states on the same `/connect` route.
**Why it happens:** The scaffold treats `ConnectPage` as the connector only.
**How to avoid:** Rename/extend `ConnectPage` to check `has_leagues`: if false, render the conversational onboarding flow; if true, render My Connections page. Per UI-SPEC Section 5C, "Connect another" opens a condensed version of the flow inline.

---

## Open Questions (RESOLVED)

1. **`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` — have these been created yet?** [RESOLVED]
   - Resolution: Plan 01-05 creates Google Cloud credentials as its first task. A human checkpoint gate is included before OAuth tests run. `.env.example` documents all three vars: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`.

2. **SMTP credentials for email delivery?** [RESOLVED]
   - Resolution: Gmail SMTP with App Password for local dev. `fastapi-mail` no-ops gracefully when `MAIL_SERVER` is empty so development can proceed without SMTP configured. Plan 01-04 creates `email_service.py` with this fallback.

3. **Exact Sleeper `keeper_flag` and `dynasty_flag` field names?** [RESOLVED]
   - Resolution: Plan 01-06 classifies draft type via `settings.type == "dynasty"` (Assumption A2) and `settings.num_keepers > 0` (Assumption A1). A live API call should be made in Wave 0 to confirm field names before writing `classify_draft()`.

4. **Postgres deployment for local dev — Docker Compose?** [RESOLVED]
   - Resolution: Plan 01-01 Task 1 creates `docker-compose.yml` at repo root with postgres, redis, app, and worker services. If the file already exists it will be updated in-place.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PostgreSQL | All DB models | Unknown | — | Docker Compose |
| Redis | Cache + rate limit | Unknown | — | Docker Compose |
| Python 3.12 | Backend | [ASSUMED present] | 3.12.x | — |
| Node.js | Frontend | [ASSUMED present] | — | — |
| PyJWT | JWT (auth) | Not installed | 2.13.0 available | pip install |
| authlib | Google OAuth | Not installed | 1.7.2 available | pip install |
| itsdangerous | Email tokens + OAuth state | Not installed | 2.2.0 available | pip install |
| fastapi-mail | Email delivery | Not installed | 1.6.5 available | pip install |
| @radix-ui/react-checkbox | League selection UI | Not installed | 1.3.5 available | npm install |
| Google OAuth credentials | AUTH-02 | Unknown | — | Create in Google Cloud Console |
| SMTP credentials | AUTH-01, AUTH-03 | Unknown | — | Gmail App Password |

**Missing dependencies with no fallback:**
- Google OAuth credentials (AUTH-02 is blocked without them)
- SMTP credentials (AUTH-01 and AUTH-03 are blocked without them)

**Missing dependencies with fallback:**
- PyJWT, authlib, itsdangerous, fastapi-mail — all pip installable
- @radix-ui/react-checkbox — npm installable

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 + pytest-asyncio 0.23.0 |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd backend && pytest tests/ -x -q` |
| Full suite command | `cd backend && pytest tests/ --cov=app --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | POST /auth/register creates unverified user | integration | `pytest tests/test_auth.py::test_register -x` | Wave 0 |
| AUTH-01 | Unverified user cannot sign in | integration | `pytest tests/test_auth.py::test_unverified_login -x` | Wave 0 |
| AUTH-02 | GET /auth/google redirects to Google | integration | `pytest tests/test_oauth.py::test_google_redirect -x` | Wave 0 |
| AUTH-03 | POST /auth/forgot-password sends email (mocked) | integration | `pytest tests/test_auth.py::test_forgot_password -x` | Wave 0 |
| AUTH-04 | /users/me returns has_leagues=False for new user | integration | `pytest tests/test_users.py::test_me_no_leagues -x` | Wave 0 |
| LC-01 | Sleeper lookup proxies Sleeper API correctly | unit (mock httpx) | `pytest tests/test_sleeper.py::test_lookup -x` | Wave 0 |
| LC-08 | Bad username returns 404 with detail | integration | `pytest tests/test_sleeper.py::test_bad_username -x` | Wave 0 |
| LC-09 | User cannot access another user's league | integration | `pytest tests/test_leagues.py::test_ownership -x` | Wave 0 |
| LC-10 | Two users import same league → one league row | integration | `pytest tests/test_leagues.py::test_dedup -x` | Wave 0 |
| LC-11 | Disconnect deletes league_member, not league | integration | `pytest tests/test_leagues.py::test_disconnect -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/ -x -q`
- **Per wave merge:** `cd backend && pytest tests/ --cov=app --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/__init__.py` — test package
- [ ] `backend/tests/conftest.py` — async test client, test DB, test Redis (mock or in-memory)
- [ ] `backend/tests/test_auth.py` — AUTH-01, AUTH-03
- [ ] `backend/tests/test_oauth.py` — AUTH-02
- [ ] `backend/tests/test_users.py` — AUTH-04
- [ ] `backend/tests/test_sleeper.py` — LC-01, LC-08 (mock httpx)
- [ ] `backend/tests/test_leagues.py` — LC-09, LC-10, LC-11
- [ ] `docker-compose.yml` at repo root — if absent (check first)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | POST /auth/login with bcrypt verify; account lockout deferred |
| V2.1 Password strength | yes | Pydantic validator: min 8 chars on register |
| V2.5 Credential recovery | yes | itsdangerous signed token, 24h expiry |
| V3 Session Management | yes | httpOnly Secure SameSite=Lax refresh cookie; 30-day rotating |
| V4 Access Control | yes | `get_current_user` dependency; `get_league_for_user` ownership check |
| V5 Input Validation | yes | Pydantic v2 on every request model |
| V6 Cryptography | yes | bcrypt for passwords (argon2 planned); PyJWT HS256 for access tokens |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credential stuffing on /auth/login | Spoofing | Rate limit: 10 req/sec burst / 100/min per IP (CONSTRAINT-013); return generic error message |
| JWT forgery | Spoofing | PyJWT HS256 with 32-byte secret; short expiry (15 min) |
| Refresh token theft via XSS | Spoofing | httpOnly cookie — JS cannot read it |
| CSRF on cookie-bearing endpoints | Tampering | SameSite=Lax cookie; explicit CSRF check on state-changing endpoints |
| Accessing another user's league | Elevation of privilege | JOIN through `league_members` filtered by `current_user.id` on every league endpoint |
| Sleeper API response injection | Tampering | All Sleeper responses validated before writing to Postgres; JSONB stores raw without executing |
| Email verification token replay | Repudiation | `itsdangerous` max_age=86400; token is single-use (flip flag + cannot re-verify) |
| Audit log missing sensitive actions | Repudiation | `AuditLog` row on: league connect, league disconnect, password change, Google link |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python-jose` for JWT | `PyJWT 2.x` | 2023 (FastAPI docs updated 2024) | Must migrate in this phase |
| `passlib` bcrypt | `argon2-cffi` (Argon2) | 2024 (passlib maintenance ended) | Keep bcrypt for MVP, tech-debt flag |
| JWT in localStorage | Short-lived JWT in memory + httpOnly refresh cookie | 2022–2023 industry shift | Refresh token NEVER in localStorage |
| `@tanstack/react-query` v4 callbacks | v5 removed `onSuccess`/`onError` in `useQuery` | v5 (2023) | Use `QueryCache` or effect hooks instead |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `keeper_flag` maps to `league.settings.num_keepers > 0` in Sleeper API response | Sleeper API / LC-03 | Classification logic wrong; may need different field name |
| A2 | `dynasty_flag` comes from `league.settings.type == "dynasty"` or similar | Sleeper API / LC-03 | Dynasty leagues misclassified as redraft |
| A3 | Sleeper usernames are stored lowercased and a `.lower()` normalization fixes case-sensitivity | Pitfall 6 | False 404s if Sleeper is actually case-sensitive on their side |
| A4 | SMTP credentials not yet configured; Gmail App Password is acceptable for dev | Environment | Email verification and password reset blocked in dev until resolved |
| A5 | Google Cloud OAuth2 credentials not yet created | Environment | AUTH-02 tasks cannot be tested until credentials exist |
| A6 | `docker-compose.yml` exists at the repo root (not listed in directory scan) | Environment | Local dev requires Postgres + Redis; if absent, Wave 0 must create compose file |
| A7 | After Google OAuth callback, backend issues JWT and passes access token back as a query param or redirect with a temporary code | Pattern 3 / AUTH-02 | Implementation design choice — resolve during planning |

**If this table is empty:** Not empty — 7 assumptions logged above that need developer confirmation.

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: docs.sleeper.com] — Sleeper API endpoints, rate limits, field names, authentication requirements
- [VERIFIED: pip registry] — Package versions for PyJWT 2.13.0, authlib 1.7.2, itsdangerous 2.2.0, fastapi-mail 1.6.5, argon2-cffi 25.1.0
- [VERIFIED: npm registry] — @radix-ui/react-checkbox 1.3.5, @radix-ui/react-label 2.1.10
- [VERIFIED: codebase] — All scaffold files (main.py, security.py, database.py, auth.ts, api.ts, App.tsx, ConnectPage.tsx, LoginPage.tsx, Layout.tsx, pyproject.toml, package.json, alembic env.py)
- [CITED: ARCHITECTURE.md] — Auth strategy, session tokens, Redis TTLs, rate limits, data model, security posture
- [CITED: UI-SPEC.md] — Complete component inventory, screen states, copywriting, accessibility baseline

### Secondary (MEDIUM confidence)
- [CITED: github.com/fastapi/fastapi/discussions/11345] — python-jose deprecation and PyJWT recommendation
- [CITED: docs.authlib.org/en/stable/client/fastapi.html] — Authlib FastAPI OAuth pattern (429 on fetch; content summarized from earlier fetch + docs.authlib.org/en/v1.3.0)
- [CITED: dev.to/elmehdiamlou] — Refresh token queue pattern for axios interceptors

### Tertiary (LOW confidence)
- [ASSUMED] — Sleeper keeper/dynasty field names in API response (verify with live API call)
- [ASSUMED] — Sleeper username case-insensitivity behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified against pip/npm registry; scaffold code read directly
- Sleeper API: HIGH — official docs fetched and verified; endpoint shapes confirmed
- Architecture patterns: HIGH — derived directly from ARCHITECTURE.md (source of truth)
- Existing scaffold inventory: HIGH — all files read directly
- Auth patterns (JWT + OAuth): MEDIUM-HIGH — documented from official authlib docs + FastAPI community consensus
- Pitfalls: MEDIUM — based on common patterns; some ASSUMED

**Research date:** 2026-06-22
**Valid until:** 2026-07-22 (stable libraries; Sleeper API has no announced breaking changes)
