# Phase 1: League Connector MVP — Pattern Map

**Mapped:** 2026-06-22
**Files analyzed:** 18 new/modified files
**Analogs found:** 14 / 18 (4 have no close analog — use RESEARCH.md patterns)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/models/user.py` | model | CRUD | `backend/app/core/database.py` (Base class) | partial — same Base, no model analog |
| `backend/app/models/league.py` | model | CRUD | `backend/app/core/database.py` (Base class) | partial — same Base, no model analog |
| `backend/app/core/security.py` | utility | request-response | `backend/app/core/security.py` (self — migrate) | exact — modify in place |
| `backend/app/core/config.py` | config | — | `backend/app/core/config.py` (self — extend) | exact — modify in place |
| `backend/app/core/deps.py` | middleware | request-response | `backend/app/api/v1/health.py` (Depends pattern) | role-match |
| `backend/app/core/cache.py` | utility | request-response | `backend/app/core/redis.py` | exact |
| `backend/app/api/v1/auth.py` | controller | request-response | `backend/app/api/v1/health.py` | role-match |
| `backend/app/api/v1/oauth.py` | controller | request-response | `backend/app/api/v1/health.py` | role-match |
| `backend/app/api/v1/users.py` | controller | request-response | `backend/app/api/v1/health.py` | role-match |
| `backend/app/api/v1/sleeper.py` | controller | request-response | `backend/app/api/v1/health.py` | role-match |
| `backend/app/api/v1/leagues.py` | controller | CRUD | `backend/app/api/v1/health.py` | role-match |
| `backend/app/services/auth_service.py` | service | request-response | `backend/app/core/security.py` | role-match |
| `backend/app/services/sleeper_client.py` | service | request-response | `backend/app/core/redis.py` (async client pattern) | partial |
| `backend/app/services/league_service.py` | service | CRUD | `backend/app/core/database.py` (session pattern) | partial |
| `backend/alembic/versions/*.py` | migration | — | `backend/alembic/env.py` | role-match |
| `frontend/src/pages/LoginPage.tsx` | component | request-response | `frontend/src/pages/LoginPage.tsx` (self — extend) | exact — modify in place |
| `frontend/src/pages/ConnectPage.tsx` | component | request-response | `frontend/src/pages/ConnectPage.tsx` (self — rewrite) | exact — rewrite in place |
| `frontend/src/store/auth.ts` | store | event-driven | `frontend/src/store/auth.ts` (self — extend) | exact — modify in place |
| `frontend/src/lib/api.ts` | utility | request-response | `frontend/src/lib/api.ts` (self — extend) | exact — modify in place |
| `frontend/src/App.tsx` | config | request-response | `frontend/src/App.tsx` (self — extend) | exact — modify in place |
| `frontend/src/components/Layout.tsx` | component | event-driven | `frontend/src/components/Layout.tsx` (self — extend) | exact — modify in place |
| `frontend/src/components/ui/*.tsx` | component | — | `frontend/src/pages/LoginPage.tsx` (Tailwind class patterns) | partial |

---

## Pattern Assignments

### `backend/app/models/user.py` + `backend/app/models/league.py` (model, CRUD)

**Analog:** `backend/app/core/database.py`

**Base class import pattern** (database.py lines 1–19):
```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase):
    pass
```

**Model import pattern** — `backend/app/models/__init__.py` must import all models so alembic/env.py sees them (alembic/env.py line 9):
```python
import app.models  # noqa: F401 — registers all models with Base
```
The `__init__.py` must be:
```python
from app.models.user import User, Session       # noqa: F401
from app.models.league import League, LeagueMember, Team, Roster  # noqa: F401
from app.models.audit import AuditLog           # noqa: F401
```

**SQLAlchemy 2.0 mapped_column pattern** — use `Mapped[T]` + `mapped_column()` throughout. No analog exists in the codebase yet; copy verbatim from RESEARCH.md Section "SQLAlchemy Models". Key imports:
```python
from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
```

**No model analog exists in this codebase.** Use RESEARCH.md model definitions verbatim.

---

### `backend/app/core/security.py` (utility, request-response) — MIGRATE IN PLACE

**Analog:** `backend/app/core/security.py` (existing file — migrate from `python-jose` to `PyJWT`)

**Current imports to replace** (security.py lines 1–8):
```python
# REMOVE:
from jose import JWTError, jwt

# REPLACE WITH:
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from itsdangerous import URLSafeTimedSerializer
```

**Current `create_access_token` to update** (security.py lines 19–25) — change `jwt_expire_minutes` from 7 days to 15 minutes (fix config.py too):
```python
def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
```

**Current `decode_token` to replace** (security.py lines 28–33) — split into typed exceptions:
```python
# REPLACE decode_token with:
def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except (ExpiredSignatureError, InvalidTokenError):
        return None
```

**Add new functions** (no analog — use RESEARCH.md Pattern 1):
```python
def create_email_token(email: str, salt: str = "email-verify") -> str:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    return s.dumps(email, salt=salt)

def verify_email_token(token: str, salt: str = "email-verify", max_age: int = 86400) -> str | None:
    s = URLSafeTimedSerializer(settings.app_secret_key)
    try:
        return s.loads(token, salt=salt, max_age=max_age)
    except Exception:
        return None

def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/api/v1/auth/refresh",
    )
```

**`pwd_context` stays** (security.py line 8):
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

---

### `backend/app/core/config.py` (config) — EXTEND IN PLACE

**Analog:** `backend/app/core/config.py` (existing file — add fields)

**Existing pattern** (config.py lines 1–40) — all new settings follow the same `pydantic_settings.BaseSettings` pattern:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    field_name: type = default_value
```

**Fields to add** (insert after `jwt_expire_minutes` — fix that value too):
```python
    jwt_expire_minutes: int = 15  # FIX: was 60 * 24 * 7 (7 days) — must be 15 min

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Email (fastapi-mail)
    mail_server: str = ""
    mail_port: int = 587
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@fantasyfootballhub.com"
    mail_tls: bool = True
```

---

### `backend/app/core/deps.py` (middleware, request-response)

**Analog:** `backend/app/api/v1/health.py` — shows `Depends(get_db)` and `Depends(get_redis)` pattern

**Dependency injection pattern** (health.py lines 1–9):
```python
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis

# In route: async def handler(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis))
```

**`get_current_user` dependency** (no analog — use RESEARCH.md Pattern 1):
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.security import decode_token
from app.core.database import get_db
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.get(User, user_id)
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
```

**`get_league_for_user` dependency** (RESEARCH.md Pattern 6 — ownership check):
```python
from sqlalchemy import select
from app.models.league import League, LeagueMember

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

---

### `backend/app/core/cache.py` (utility, request-response)

**Analog:** `backend/app/core/redis.py` — existing TTL constants and redis getter

**Existing pattern** (redis.py lines 1–30):
```python
from redis.asyncio import Redis, from_url
from app.core.config import settings

_redis: Redis | None = None

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.redis_url, decode_responses=True)
    return _redis

class CacheTTL:
    LEAGUE_SETTINGS = 300
    ROSTER = 120
```

**Extend with Phase 1 TTLs** — reuse the `CacheTTL` class in `redis.py` or create `cache.py` with key-builder helpers:
```python
# cache.py — key builder helpers
class CacheKey:
    @staticmethod
    def sleeper_user(username: str) -> str:
        return f"sleeper:user:{username.lower()}"

    @staticmethod
    def sleeper_leagues(user_id: str, season: str) -> str:
        return f"sleeper:leagues:{user_id}:{season}"

    @staticmethod
    def league_settings(league_id: str) -> str:
        return f"league:{league_id}:settings"

    @staticmethod
    def league_members(league_id: str) -> str:
        return f"league:{league_id}:members"

    @staticmethod
    def league_rosters(league_id: str, week: int) -> str:
        return f"league:{league_id}:rosters:{week}"

    @staticmethod
    def nfl_state() -> str:
        return "nfl:state"

    @staticmethod
    def rate_limit_sleeper(user_id: str) -> str:
        return f"ratelimit:sleeper:{user_id}"

# Phase 1 TTLs (seconds) — matches ARCHITECTURE.md Section 5
class CacheTTL:
    SLEEPER_USER = 300        # 5 min
    SLEEPER_LEAGUES = 600     # 10 min
    LEAGUE_SETTINGS = 21600   # 6 hours
    LEAGUE_MEMBERS = 21600    # 6 hours
    LEAGUE_ROSTERS = 1800     # 30 min
    NFL_STATE = 3600          # 1 hour
```

---

### `backend/app/api/v1/auth.py` + `oauth.py` + `users.py` (controller, request-response)

**Analog:** `backend/app/api/v1/health.py` — only existing route file

**Router pattern** (health.py lines 1–9):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}
```

**All new routers follow the same pattern:**
```python
# auth.py
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, set_refresh_cookie
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    ...

@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    ...
```

**Registration in v1 `__init__.py`** — copy the existing pattern (v1/__init__.py lines 1–6):
```python
from fastapi import APIRouter
from app.api.v1 import health, auth, oauth, users, sleeper, leagues

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(oauth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(sleeper.router, tags=["sleeper"])
router.include_router(leagues.router, tags=["leagues"])
```

**`main.py` addition** — `SessionMiddleware` for Google OAuth (add after CORS middleware, before routes):
```python
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)
```

---

### `backend/app/api/v1/sleeper.py` + `backend/app/api/v1/leagues.py` (controller, CRUD)

**Analog:** `backend/app/api/v1/health.py` (router pattern) + `backend/app/core/redis.py` (redis dependency)

**Protected route pattern** — combine `get_db` + `get_redis` + `get_current_user` (all patterns already seen):
```python
from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sleeper", tags=["sleeper"])

@router.get("/lookup")
async def lookup(
    username: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    ...
```

**Error response pattern** (health.py shows no error handling — use this standard):
```python
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Sleeper user not found")
raise HTTPException(status_code=422, detail="No active leagues found for that username")
```

---

### `backend/app/services/sleeper_client.py` (service, request-response)

**Analog:** `backend/app/core/redis.py` — async client singleton pattern

**Existing async client pattern** (redis.py lines 1–19):
```python
from redis.asyncio import Redis, from_url

_redis: Redis | None = None

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.redis_url, decode_responses=True)
    return _redis
```

**Sleeper client follows class-based pattern instead** (RESEARCH.md Pattern 4 — httpx):
```python
import httpx
from app.core.config import settings
from app.core.logging import logger

class SleeperNotFound(Exception):
    pass

class SleeperClient:
    BASE = settings.sleeper_api_base  # "https://api.sleeper.app/v1"

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def get_user(self, username: str) -> dict:
        r = await self.http.get(f"{self.BASE}/user/{username.strip().lower()}")
        if r.status_code == 404:
            raise SleeperNotFound(username)
        r.raise_for_status()
        return r.json()

    # ... other methods per RESEARCH.md Pattern 4

# FastAPI dependency
async def get_sleeper_client() -> SleeperClient:
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield SleeperClient(client)
```

**Note:** `sleeper_api_base` is already in `config.py` (line 28). Use it.

---

### `backend/app/services/league_service.py` (service, CRUD)

**Analog:** `backend/app/core/database.py` — async session + transaction pattern

**Transaction pattern** (database.py lines 22–30):
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Atomic import pattern** (RESEARCH.md Pattern 5 — no analog in codebase):
```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

async def import_league(league_id: str, current_user: User, db: AsyncSession, redis: Redis) -> League:
    # Collect all Sleeper data BEFORE opening DB transaction (LC-08)
    league_data = await sleeper.get_league(league_id)
    rosters = await sleeper.get_rosters(league_id)
    members = await sleeper.get_users(league_id)

    async with db.begin():  # rollback on any failure
        stmt = pg_insert(League).values(...).on_conflict_do_update(
            index_elements=["host_platform", "host_league_id", "season"],
            set_={"last_synced_at": datetime.now(UTC)},
        ).returning(League)
        league = (await db.execute(stmt)).scalar_one()
        ...

    # After commit: cache
    await redis.set(CacheKey.league_settings(str(league.id)), json.dumps(league_data), ex=CacheTTL.LEAGUE_SETTINGS)
    return league
```

---

### `backend/alembic/versions/*.py` (migration)

**Analog:** `backend/alembic/env.py` — shows async migration pattern

**Alembic env pattern** (env.py lines 1–45) — already configured. After writing models, run:
```bash
cd backend && alembic revision --autogenerate -m "phase1_auth_league"
```
The generated file will follow standard Alembic `upgrade()` / `downgrade()` structure. No manual migration file pattern needed — autogenerate handles it once `app.models.__init__` imports all models.

**env.py critical line** (env.py line 9) — models must be imported here or in `app/models/__init__.py`:
```python
import app.models  # noqa: F401 — registers all models with Base
```

---

### `frontend/src/pages/LoginPage.tsx` (component, request-response) — EXTEND IN PLACE

**Analog:** `frontend/src/pages/LoginPage.tsx` (self)

**Existing pattern** (LoginPage.tsx lines 1–96) — all patterns to copy from:

**State + form pattern** (lines 1–29):
```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { api } from '@/lib/api'

const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

async function handleSubmit(e: React.FormEvent) {
  e.preventDefault()
  setError(null)
  setLoading(true)
  try {
    const { data } = await api.post(endpoint, { email, password })
    setAuth(data.access_token, data.user_id)
    navigate('/team', { replace: true })
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Something went wrong')
  } finally {
    setLoading(false)
  }
}
```

**Error display pattern** (lines 69–73) — copy exactly:
```tsx
{error && (
  <p className="text-danger text-sm bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
    {error}
  </p>
)}
```

**Loading button pattern** (lines 75–82):
```tsx
<button
  type="submit"
  disabled={loading}
  className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-2.5 transition-colors"
>
  {loading ? 'Please wait…' : isRegister ? 'Create Account' : 'Sign In'}
</button>
```

**Input field pattern** (lines 47–55) — note: UI-SPEC requires `min-h-[44px]`, update from current `py-2.5`:
```tsx
<input
  type="email"
  required
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  className="w-full bg-surface border border-border rounded-lg px-3 py-3 text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
/>
```

**New additions needed in LoginPage:**
- Google OAuth button (above form, secondary style)
- "Forgot password?" link + inline panel below password field
- Post-register email verification state (replace form with Mail icon + copy)
- `aria-describedby` linking errors to fields

---

### `frontend/src/pages/ConnectPage.tsx` (component, request-response) — REWRITE IN PLACE

**Analog:** `frontend/src/pages/ConnectPage.tsx` (self — rewrite, not extend)

**State machine pattern to keep** (ConnectPage.tsx lines 1–18):
```tsx
import { useState } from 'react'
import { api } from '@/lib/api'

type Step = 'platform' | 'username' | 'leagues' | 'importing' | 'done'

const [step, setStep] = useState<Step>('platform')
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
```

**API call pattern to keep** (lines 23–36):
```tsx
async function fetchLeagues() {
  if (!username.trim()) return
  setLoading(true)
  setError(null)
  try {
    const { data } = await api.get(`/sleeper/lookup?username=${encodeURIComponent(username.trim().toLowerCase())}`)
    setLeagues(data)
    setStep('leagues')
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Could not find that username')
  } finally {
    setLoading(false)
  }
}
```

**Multi-select leagues state** — new addition (ConnectPage currently imports single league):
```tsx
const [selectedLeagueIds, setSelectedLeagueIds] = useState<Set<string>>(new Set())

function toggleLeague(id: string) {
  setSelectedLeagueIds(prev => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })
}
```

**Disabled platform button pattern** (ConnectPage.tsx lines 75–90):
```tsx
<button
  disabled
  className="w-full bg-surface border border-border/50 rounded-xl p-4 text-left opacity-40 cursor-not-allowed"
>
  <p className="font-semibold text-text">Yahoo Fantasy</p>
  <p className="text-sm text-muted">Coming soon</p>
</button>
```

**Layout upgrade** — current layout is a simple div stack; UI-SPEC requires three-zone layout (top bar / chat scroll / fixed input row). The top-level shell becomes:
```tsx
<div className="flex flex-col h-screen bg-bg">
  {/* Zone 1: Top bar 52px */}
  <div className="h-[52px] flex items-center justify-center px-4 bg-surface border-b border-border shrink-0">
    <span className="text-base font-semibold text-text">FantasyHub</span>
    {!hasLeagues && (
      <button className="absolute right-4 text-sm text-muted hover:text-text">Skip setup</button>
    )}
  </div>
  {/* Zone 2: Chat scroll area */}
  <div className="flex-1 overflow-y-auto">
    <div className="max-w-[600px] w-full mx-auto px-5 py-6 space-y-2">
      {/* chat bubbles */}
    </div>
  </div>
  {/* Zone 3: Input row (fixed above bottom nav) */}
</div>
```

---

### `frontend/src/store/auth.ts` (store, event-driven) — EXTEND IN PLACE

**Analog:** `frontend/src/store/auth.ts` (self)

**Existing pattern** (auth.ts lines 1–21) — extend the interface and store:
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  // ADD:
  hasLeagues: boolean
  setAuth: (token: string, userId: string) => void
  // ADD:
  setHasLeagues: (value: boolean) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      hasLeagues: false,           // new
      setAuth: (token, userId) => set({ token, userId }),
      setHasLeagues: (value) => set({ hasLeagues: value }),  // new
      clearAuth: () => set({ token: null, userId: null, hasLeagues: false }),
    }),
    { name: 'ffhub-auth' },
  ),
)
```

**Critical constraint:** `hasLeagues` is safe to persist. The refresh token MUST NOT be added to this store — it lives only in the httpOnly cookie.

---

### `frontend/src/lib/api.ts` (utility, request-response) — EXTEND IN PLACE

**Analog:** `frontend/src/lib/api.ts` (self)

**Existing interceptors to keep** (api.ts lines 1–24):
```typescript
import axios from 'axios'
import { useAuthStore } from '@/store/auth'

export const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,  // ADD: needed for httpOnly refresh token cookie
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor (lines 9–13) — keep as-is
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

**Replace the current 401 handler** (api.ts lines 15–23) with the refresh retry queue (RESEARCH.md Pattern 7):
```typescript
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
        const { data } = await api.post('/auth/refresh')
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

---

### `frontend/src/App.tsx` (config) — EXTEND IN PLACE

**Analog:** `frontend/src/App.tsx` (self)

**Existing `RequireAuth` pattern** (App.tsx lines 10–14) — copy for new `RequireLeague` guard:
```tsx
function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

// New guard — redirect to /connect if no leagues
function RequireLeague({ children }: { children: React.ReactNode }) {
  const hasLeagues = useAuthStore((s) => s.hasLeagues)
  if (!hasLeagues) return <Navigate to="/connect" replace />
  return <>{children}</>
}
```

**Route structure to extend** (App.tsx lines 16–37):
```tsx
<Route path="team" element={<RequireLeague><TeamPage /></RequireLeague>} />
<Route path="draft" element={<RequireLeague><DraftPage /></RequireLeague>} />
<Route path="trades" element={<RequireLeague><TradePage /></RequireLeague>} />
```

---

### `frontend/src/components/Layout.tsx` (component, event-driven) — EXTEND IN PLACE

**Analog:** `frontend/src/components/Layout.tsx` (self)

**Existing tab rendering pattern** (Layout.tsx lines 5–47) — add `disabled` prop check using `hasLeagues`:
```tsx
import { useAuthStore } from '@/store/auth'

// In component:
const hasLeagues = useAuthStore((s) => s.hasLeagues)

// Per UI-SPEC Section 6 — Team, Draft, Trades, More disabled until first league:
const REQUIRES_LEAGUE = ['/team', '/draft', '/trades', '/more']

// In tab render:
{tabs.map(({ to, icon: Icon, label }) => {
  const isDisabled = !hasLeagues && REQUIRES_LEAGUE.includes(to)
  return (
    <NavLink
      key={to}
      to={to}
      className={({ isActive }) =>
        cn(
          'flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg transition-colors',
          isDisabled ? 'opacity-40 pointer-events-none text-muted' :
          isActive ? 'text-accent' : 'text-muted hover:text-text',
        )
      }
      aria-disabled={isDisabled}
      tabIndex={isDisabled ? -1 : undefined}
    >
      <Icon size={22} strokeWidth={1.75} />
      <span className="text-xs font-semibold">{label}</span>
    </NavLink>
  )
})}
```

Note: UI-SPEC says `text-[10px] font-medium` in current Layout; update to `text-xs font-semibold` per UI-SPEC Section 6.

---

### `frontend/src/components/ui/*.tsx` (component) — NEW FILES

**Analog:** `frontend/src/pages/LoginPage.tsx` + `frontend/src/components/Layout.tsx` (Tailwind class patterns) + `frontend/src/lib/utils.ts` (cn utility)

**`cn` utility is already available** (utils.ts lines 1–5):
```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Button component pattern** — derives from LoginPage button styles:
```tsx
// src/components/ui/Button.tsx
import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
}

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors disabled:opacity-50',
        variant === 'primary' && 'bg-accent hover:bg-accent/90 text-white',
        variant === 'secondary' && 'bg-raised border border-border text-text hover:border-accent',
        variant === 'ghost' && 'text-accent hover:underline',
        variant === 'danger' && 'bg-danger text-white hover:bg-danger/90',
        className,
      )}
      {...props}
    />
  )
}
```

**Input component pattern** — derives from LoginPage input styles:
```tsx
// src/components/ui/Input.tsx
export function Input({ className, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { error?: boolean }) {
  return (
    <input
      className={cn(
        'w-full bg-raised border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted',
        'focus:outline-none focus:border-accent transition-colors min-h-[44px]',
        error ? 'border-danger' : 'border-border',
        className,
      )}
      {...props}
    />
  )
}
```

**Chat bubble pattern** — derives from UI-SPEC Section 5B color rules:
```tsx
// src/components/ui/ChatBubble.tsx
export function ChatBubble({ variant, children }: { variant: 'app' | 'user'; children: React.ReactNode }) {
  return (
    <div className={cn(
      'rounded-[20px] py-3 px-4 text-sm max-w-[85%] animate-fade-in',
      variant === 'app' && 'bg-surface border border-border text-text self-start',
      variant === 'user' && 'bg-accent text-white self-end ml-auto',
    )}>
      {children}
    </div>
  )
}
```

---

## Shared Patterns

### Authentication Guard (backend)
**Source:** `backend/app/core/deps.py` (to be created)
**Apply to:** All routes in `auth.py`, `users.py`, `sleeper.py`, `leagues.py`
```python
# Route signature pattern:
async def handler(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
```

### Async DB Session
**Source:** `backend/app/core/database.py` lines 22–30
**Apply to:** All API route handlers and service functions that write to Postgres
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Redis Dependency
**Source:** `backend/app/core/redis.py` lines 1–19
**Apply to:** `sleeper.py`, `leagues.py` routes and `sleeper_client.py`, `league_service.py`
```python
from app.core.redis import get_redis
# In route: redis: Redis = Depends(get_redis)
```

### Structlog Logging
**Source:** `backend/app/core/logging.py` lines 24–25
**Apply to:** All service files and routes that perform significant operations
```python
from app.core.logging import logger
logger.info("league.import", league_id=league_id, user_id=str(current_user.id))
```

### Pydantic Request/Response Models
**Source:** Pattern established by health.py + RESEARCH.md
**Apply to:** All POST/PUT route bodies in auth.py, users.py, sleeper.py, leagues.py
```python
from pydantic import BaseModel, EmailStr

class SomeRequest(BaseModel):
    field: str

class SomeResponse(BaseModel):
    id: str
    # ... fields

# In route:
@router.post("/endpoint", response_model=SomeResponse)
async def handler(body: SomeRequest, ...):
```

### Settings Access
**Source:** `backend/app/core/config.py` lines 39–40
**Apply to:** All files that need environment-specific values
```python
from app.core.config import settings
# Access: settings.jwt_secret, settings.is_production, etc.
```

### `cn` Utility + Tailwind Composition
**Source:** `frontend/src/lib/utils.ts`
**Apply to:** All new `src/components/ui/*.tsx` files
```typescript
import { cn } from '@/lib/utils'
// Usage: className={cn('base-classes', condition && 'conditional-class', externalClassName)}
```

### React Query Data Fetching
**Source:** RESEARCH.md Section "Standard Stack" (v5 — no `onSuccess`/`onError` in `useQuery`)
**Apply to:** `ConnectionsPage.tsx` (My Connections list), any page fetching server data
```typescript
import { useQuery } from '@tanstack/react-query'
// v5 pattern — use effects for side effects, not onSuccess:
const { data, isLoading, isError } = useQuery({
  queryKey: ['leagues', 'mine'],
  queryFn: () => api.get('/leagues/mine').then(r => r.data),
})
```

---

## No Analog Found

Files with no close match in the codebase — use RESEARCH.md patterns exclusively:

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/models/user.py` | model | CRUD | No SQLAlchemy models exist yet; `app/models/` is empty |
| `backend/app/models/league.py` | model | CRUD | Same — no model analog |
| `backend/app/api/v1/oauth.py` | controller | request-response | No OAuth flow exists; `authlib` + `SessionMiddleware` pattern is new |
| `backend/app/services/email_service.py` | service | event-driven | No email delivery exists; `fastapi-mail` pattern is new |
| `backend/app/workers/league_purge.py` | worker | event-driven | No `arq` workers exist; background job pattern is new |
| `backend/tests/conftest.py` + `test_*.py` | test | — | No tests exist in the codebase yet |

---

## Key Cross-Cutting Constraints

These are not optional patterns — they are architectural requirements from RESEARCH.md:

1. **Refresh token never in localStorage or Zustand:** httpOnly cookie only. The `/auth/refresh` endpoint response body contains only `access_token`. Never add `refresh_token` to `AuthState`.

2. **Sleeper API always called from backend:** No direct Sleeper API calls from React. All calls go through `/api/v1/sleeper/*` endpoints.

3. **League import must be atomic:** All Sleeper API calls complete BEFORE `async with db.begin()` opens. Any API failure prevents the transaction from opening. Satisfies LC-08.

4. **Ownership filter on all league endpoints:** Every league endpoint joins through `league_members` filtered by `current_user.id`. Never fetch by `league_id` alone.

5. **PyJWT migration is all-or-nothing:** When adding `PyJWT`, remove `python-jose` in the same task. Both have `jwt.encode()` but different exception classes — mixing them creates silent bugs.

6. **`jwt_expire_minutes` fix:** Change from `60 * 24 * 7` (7 days) to `15` in `config.py` when building auth. This is a breaking config change, not a bug fix.

---

## Metadata

**Analog search scope:** `backend/app/`, `frontend/src/` — all Python and TypeScript source files
**Files scanned:** 15 source files read directly
**Pattern extraction date:** 2026-06-22
