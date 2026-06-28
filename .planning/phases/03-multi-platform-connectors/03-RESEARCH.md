# Phase 3: Multi-Platform Connectors — Research

**Researched:** 2026-06-28
**Domain:** Yahoo Fantasy Sports API (OAuth 2.0), ESPN Fantasy API (unofficial cookie-based), Player ID cross-mapping, credential encryption, per-platform rate limiting
**Confidence:** MEDIUM — Yahoo OAuth is HIGH confidence from official docs; ESPN is MEDIUM from community sources; player ID mapping is MEDIUM; rate limits for both platforms are LOW (undocumented)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MP-01 | Yahoo OAuth connector — consent flow, encrypted refresh token, leagues listed for import | Yahoo OAuth endpoints verified; authlib already in pyproject.toml; User.envelope_key already in schema for encryption |
| MP-02 | Yahoo leagues data parity with Sleeper (settings, rosters, scoring) | Yahoo Fantasy API endpoint structure identified; scoring_settings, roster_positions patterns documented |
| MP-03 | ESPN private league — SWID + espn_s2 cookie paste, stored encrypted, expiration warning | ESPN v3 API cookie auth confirmed; Fernet encryption pattern identified; detect expiry via 401 response |
| MP-04 | ESPN public league — league ID only, read-only connection | ESPN endpoints work without cookies for public leagues; connection marked read_only |
| MP-05 | ESPN data parity + validation for expired cookies / bad league IDs | ESPN view parameters documented; validation at import time against live API |
| MP-06 | Expired credential banner on every page when sync detects expired auth | Requires UserCredential.is_healthy; arq sync worker marks unhealthy; frontend global state |
| MP-07 | Per-platform rate limits enforced in Redis; soft toast, cached value | Existing ratelimit:sleeper:{user_id} pattern in CacheKey; extend with yahoo/espn variants |
| MP-08 | Player ID cross-map Yahoo/ESPN/Sleeper — single unified record | dynastyprocess/ffb_ids CSV confirmed with all three ID systems; fallback fuzzy match strategy |
| MP-09 | Keeper count, cost, contract years captured; unmodeled rules report | Yahoo/ESPN settings endpoints expose keeper fields; store in existing League.scoring_rules JSONB |
</phase_requirements>

---

## Summary

Phase 3 adds two platform connectors — Yahoo Fantasy Sports (OAuth 2.0) and ESPN Fantasy Football (unofficial cookie-based API) — so that connected leagues from any of the three platforms open in the same Team Manager experience. The core technical challenges are: (1) Yahoo's standard OAuth Authorization Code flow, which the existing `authlib` library handles; (2) ESPN's entirely unofficial API, which uses session cookies and has no official documentation or rate limit guarantees; (3) storing encrypted credentials using the `cryptography.Fernet` scheme keyed by each user's existing `envelope_key`; (4) cross-mapping player IDs across three ID spaces using a community-maintained CSV dataset; and (5) detecting and surfacing expired credentials as a global app-wide banner.

The existing codebase provides clean templates for all three work streams: `SleeperClient` establishes the HTTP client wrapper pattern to replicate, `league_service.import_league()` establishes the atomic fetch-then-write pattern, `CacheKey.rate_limit_sleeper()` establishes the rate-limit key pattern to extend, and `User.envelope_key` is already in the schema for per-user encryption. No new major Python libraries are needed — authlib (already present) covers Yahoo OAuth, httpx (already present) covers ESPN API calls, and cryptography (already a transitive dependency of authlib) provides Fernet encryption.

**Primary recommendation:** Mirror the SleeperClient/league_service pattern exactly for both Yahoo and ESPN. Build custom thin clients rather than introducing yfpy or espn-api package dependencies — those libraries impose their own abstractions and version coupling that conflicts with the established codebase pattern.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Yahoo OAuth consent redirect | Frontend Server (FastAPI route) | Browser | FastAPI generates the redirect; authlib manages state/PKCE |
| Yahoo OAuth callback + token storage | API / Backend | — | Code exchange and encrypted storage happen server-side; no token touches the browser |
| ESPN cookie input form | Browser (React) | — | User pastes SWID/espn_s2 from their browser; form submits to API |
| ESPN credential encryption + storage | API / Backend | Database | Fernet encrypt on the way in; stored in user_credentials table |
| Yahoo/ESPN API data fetch | API / Backend | — | All platform API calls originate from backend; never from browser |
| Player ID cross-map seed load | Background (arq) | Database | One-time + weekly refresh via arq task; stored in player_cross_map table |
| Expired credential detection | Background (arq) | API / Backend | Sync worker catches 401; marks UserCredential.is_healthy=False |
| Expired credential banner | Browser (React) | API / Backend | Frontend checks credential health in global state; banner shows on all pages |
| Per-platform rate limiting | API / Backend | Database (Redis) | Fixed-window counter in Redis; checked before every platform API call |
| Keeper/scoring rule normalization | API / Backend | — | Extract and normalize into existing League.scoring_rules JSONB at import time |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| authlib | ≥1.7.2 | Yahoo OAuth 2.0 Authorization Code flow | Already in pyproject.toml; used for Google OAuth in Phase 1; handles state, PKCE, token refresh |
| httpx | ≥0.27.0 | ESPN API HTTP client (cookie-based) | Already in pyproject.toml; used by SleeperClient; async-native |
| cryptography | ≥42.0.0 | Fernet encryption for stored refresh tokens and ESPN cookies | Transitive via authlib; add explicit dependency; Fernet is standard for symmetric token encryption |
| redis[hiredis] | ≥5.0.0 | Per-platform rate-limit counters and credential health cache | Already in pyproject.toml; existing rate_limit_sleeper pattern to extend |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncpg | ≥0.29.0 | PostgreSQL driver (JSONB) | Already in pyproject.toml; stores credentials_encrypted as LargeBinary |
| structlog | ≥24.2.0 | Structured logging for OAuth events and sync failures | Already in pyproject.toml; follow existing logger pattern |
| arq | ≥0.26.0 | Background sync tasks for Yahoo/ESPN and player ID map refresh | Already in pyproject.toml; add new task functions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom YahooClient | yfpy (v17.0.0) | yfpy is comprehensive but opinionated; requires its own token storage; incompatible with our async authlib OAuth flow; hard to test |
| Custom ESPNClient | espn-api (v0.46.0) | espn-api v0.46 is synchronous; would need thread executor; adds version coupling we don't control |
| Fernet (symmetric) | AES-GCM via cryptography.hazmat | Fernet is simpler to use correctly, handles MAC verification automatically, sufficient for this use case |
| Fixed-window rate limit | Sliding window (sorted set) | Fixed window is simpler to implement atomically; for ~100 req/10min budgets, the window boundary edge case is acceptable |

**Installation — new explicit dependency only:**
```bash
pip install "cryptography>=42.0.0"
```
Update `pyproject.toml` to add `"cryptography>=42.0.0"` to the dependencies list (currently only transitively included via authlib).

**Version verification:**
```bash
pip index versions cryptography  # 49.0.0 is current as of 2026-06-28
pip index versions espn-api       # 0.46.0 current (for reference only — not adding)
```
[VERIFIED: pip registry, 2026-06-28]

---

## Architecture Patterns

### System Architecture Diagram

```
Browser                      FastAPI Routes              Backend Services           External APIs
────────                     ──────────────              ─────────────────          ─────────────
Yahoo connect click  ──────► POST /auth/yahoo ──────────► authlib OAuth redirect ──► Yahoo consent
                                                                                       page
                    ◄─────────────────────────────────── Yahoo callback with code ◄──
                             POST /auth/yahoo/callback
                               ├─ exchange code for tokens (authlib)
                               ├─ encrypt refresh_token (Fernet)
                               └─ upsert UserCredential (platform=yahoo) ──────────► PostgreSQL

ESPN cookie paste   ──────► POST /espn/connect ─────────► ESPNClient.verify_league() ──► ESPN API
  {swid, espn_s2,              ├─ validate credentials live                           (unofficial)
   league_id}                  ├─ encrypt cookies (Fernet)
                               └─ upsert UserCredential (platform=espn)

League import       ──────► POST /yahoo/import ─────────► YahooClient.get_league()   ──► Yahoo API
  {league_id}                  │   league_service.import_yahoo_league()
                               │   ├─ fetch settings, roster_positions, scoring_settings
                               │   ├─ fetch teams + rosters
                               │   ├─ map Yahoo player_ids → internal via player_cross_map
                               │   └─ upsert League, Team, Roster (same pattern as Sleeper)

arq worker          ──────  sync_yahoo_league()  ───────► YahooClient (with stored token)
  (scheduled sync)             ├─ if 401: UserCredential.is_healthy = False ──────► PostgreSQL
                               └─ on success: update League, Roster in DB

               ─────────────────────────────────────────────────────
arq worker (weekly) seed_player_cross_map() ──────────────────────► dynastyprocess CSV URL
                             └─ bulk upsert player_cross_map table ──► PostgreSQL

Frontend global     ◄─────── GET /users/me (or leagues) ───────────── UserCredential.is_healthy
  banner                      returns is_healthy per platform          from DB
```

### Recommended Project Structure
```
backend/app/
├── services/
│   ├── sleeper_client.py     # existing — template for new clients
│   ├── yahoo_client.py       # new — YahooClient mirrors SleeperClient
│   ├── espn_client.py        # new — ESPNClient mirrors SleeperClient
│   ├── credential_service.py # new — encrypt/decrypt/validate credentials
│   ├── player_id_mapper.py   # new — PlayerIDMapper using player_cross_map table
│   └── league_service.py     # extend with import_yahoo_league, import_espn_league
├── api/v1/
│   ├── yahoo.py              # new — /yahoo/leagues, /yahoo/import
│   ├── espn.py               # new — /espn/connect, /espn/import
│   └── oauth.py              # extend with /auth/yahoo, /auth/yahoo/callback
├── models/
│   ├── league.py             # existing (no changes needed)
│   ├── user.py               # existing (no changes needed)
│   └── credential.py         # new — UserCredential model
├── workers/
│   └── platform_sync.py      # new arq tasks for Yahoo/ESPN sync + player map
├── core/
│   └── cache.py              # extend CacheKey + CacheTTL for yahoo/espn
└── data/
    └── player_cross_map_seed.py  # helper for CSV download + bulk insert
alembic/versions/
└── 002_phase3_credentials_playermap.py  # new migration
```

### Pattern 1: Credential Encryption with Fernet

**What:** Encrypt Yahoo refresh tokens and ESPN cookie strings using each user's `envelope_key` and `cryptography.Fernet`.

**When to use:** Any time a platform credential (token, cookie) is written to or read from the `user_credentials` table.

**Key constraint:** `User.envelope_key` is `bytes | None`. Generate a 32-byte key on first platform connection if not already set. The Fernet key is URL-safe base64 of those bytes.

```python
# Source: cryptography.io/en/latest/fernet/ [CITED]
import base64
import os
from cryptography.fernet import Fernet
from app.models.credential import UserCredential
from app.models.user import User

def _get_fernet(user: User) -> Fernet:
    if user.envelope_key is None:
        user.envelope_key = os.urandom(32)
    return Fernet(base64.urlsafe_b64encode(user.envelope_key))

def encrypt_credential(user: User, plaintext: str) -> bytes:
    return _get_fernet(user).encrypt(plaintext.encode())

def decrypt_credential(user: User, ciphertext: bytes) -> str:
    return _get_fernet(user).decrypt(ciphertext).decode()
```

### Pattern 2: Yahoo OAuth 2.0 via authlib (Authorization Code Flow)

**What:** Register Yahoo as an OAuth provider in the existing `authlib` `OAuth` object. Yahoo uses the same Authorization Code flow as Google.

**When to use:** Yahoo platform connector setup.

```python
# Source: developer.yahoo.com/oauth2/guide/flows_authcode/ [CITED]
# authlib docs [ASSUMED pattern — mirrors existing google oauth.register]
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()  # existing object in oauth.py
oauth.register(
    name="yahoo",
    client_id=settings.yahoo_client_id,
    client_secret=settings.yahoo_client_secret,
    authorize_url="https://api.login.yahoo.com/oauth2/request_auth",
    access_token_url="https://api.login.yahoo.com/oauth2/get_token",
    client_kwargs={"scope": "fspt-r"},  # read-only; use fspt-w for TM-16 write
)

# Callback: exchange code, store refresh_token encrypted
async def yahoo_callback(request: Request, db: AsyncSession, user: User):
    token = await oauth.yahoo.authorize_access_token(request)
    refresh_token = token["refresh_token"]
    credential = encrypt_credential(user, json.dumps({
        "access_token": token["access_token"],
        "refresh_token": refresh_token,
        "expires_at": token["expires_at"],
    }))
    # upsert UserCredential(user_id, platform="yahoo", credentials_encrypted)
```

**Token refresh flow:**
```python
# Source: developer.yahoo.com/oauth2/guide/ [CITED]
# Grant type: refresh_token; POST to https://api.login.yahoo.com/oauth2/get_token
# Headers: Authorization: Basic base64(client_id:client_secret)
# Body: grant_type=refresh_token&refresh_token={token}
# Returns new access_token (1-hour lifetime) + new refresh_token
```

### Pattern 3: ESPN API Client (Cookie-Based)

**What:** Thin HTTP client for ESPN's unofficial API. Passes SWID and espn_s2 as cookies.

**When to use:** All ESPN data fetches.

```python
# Source: stmorse.github.io/journal/espn-fantasy-v3.html [CITED]
# Base URL changed April 2024; current URL is lm-api-reads domain
ESPN_BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

class ESPNClient:
    def __init__(self, http: httpx.AsyncClient, swid: str | None, espn_s2: str | None):
        self.http = http
        self.cookies = {}
        if swid and espn_s2:
            self.cookies = {"SWID": swid, "espn_s2": espn_s2}

    async def get_league(self, league_id: str, year: int) -> dict:
        views = ["mSettings", "mRoster", "mTeam", "mMatchupScore", "mStandings"]
        params = [("view", v) for v in views]
        url = f"{ESPN_BASE}/seasons/{year}/segments/0/leagues/{league_id}"
        r = await self.http.get(url, params=params, cookies=self.cookies)
        if r.status_code == 401:
            raise ESPNAuthExpired("ESPN cookies expired or invalid")
        if r.status_code == 404:
            raise ESPNLeagueNotFound(league_id)
        r.raise_for_status()
        return r.json()
```

### Pattern 4: Yahoo Fantasy API Client

**What:** Thin HTTP wrapper for the Yahoo Fantasy API. Requires a valid access token on every request.

```python
# Source: yahoo-fantasy-node-docs.vercel.app + yfpy.uberfastman.com [CITED]
YAHOO_FANTASY_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"

class YahooClient:
    def __init__(self, http: httpx.AsyncClient, access_token: str):
        self.http = http
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",  # required — default is XML
        }

    async def get_user_leagues(self, game_key: str = "nfl") -> dict:
        # Returns all leagues for the authenticated user in the current season
        url = f"{YAHOO_FANTASY_BASE}/users;use_login=1/games;game_codes={game_key}/leagues"
        r = await self.http.get(url, headers=self.headers)
        if r.status_code == 401:
            raise YahooAuthExpired("Yahoo access token expired")
        r.raise_for_status()
        return r.json()

    async def get_league_settings(self, league_key: str) -> dict:
        # league_key format: "{game_key}.l.{league_id}" e.g. "461.l.123456"
        url = f"{YAHOO_FANTASY_BASE}/league/{league_key}/settings"
        r = await self.http.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    async def get_team_roster(self, team_key: str, week: int) -> dict:
        # team_key: "{game_key}.l.{league_id}.t.{team_id}"
        url = f"{YAHOO_FANTASY_BASE}/team/{team_key}/roster;type=week;week={week}"
        r = await self.http.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()
```

### Pattern 5: Rate Limiting (Redis Fixed Window)

**What:** Fixed-window counter in Redis matching the existing `ratelimit:sleeper:{user_id}` pattern.

```python
# Source: existing CacheKey.rate_limit_sleeper pattern [VERIFIED: codebase grep]
# Extend CacheKey:
class CacheKey:
    @staticmethod
    def rate_limit_yahoo(user_id: str) -> str:
        return f"ratelimit:yahoo:{user_id}"

    @staticmethod
    def rate_limit_espn(user_id: str) -> str:
        return f"ratelimit:espn:{user_id}"

# Usage in route handler:
async def check_rate_limit(redis: Redis, key: str, limit: int, window: int) -> bool:
    """Returns True if within limit, False if exceeded. Atomic incr+expire."""
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)
    return count <= limit

# Budgets (conservative — platform limits undocumented):
YAHOO_RATE_LIMIT = 200    # per 10 minutes per user [ASSUMED]
ESPN_RATE_LIMIT = 100     # per 10 minutes per user [ASSUMED]
RATE_WINDOW_SECONDS = 600 # 10-minute window
```

### Pattern 6: Player ID Cross-Map Lookup

**What:** Resolve a platform player ID to its equivalents in other platforms.

```python
# Source: codebase design [ASSUMED]
class PlayerIDMapper:
    """Translates player IDs across Yahoo, ESPN, and Sleeper.

    Primary lookup: direct match in player_cross_map table.
    Fallback: fuzzy match on (name, position) using difflib.SequenceMatcher.
    """
    async def yahoo_to_sleeper(self, db: AsyncSession, yahoo_id: str) -> str | None:
        result = await db.execute(
            select(PlayerCrossMap).where(PlayerCrossMap.yahoo_id == yahoo_id)
        )
        row = result.scalar_one_or_none()
        return row.sleeper_id if row else None

    async def espn_to_sleeper(self, db: AsyncSession, espn_id: str) -> str | None:
        result = await db.execute(
            select(PlayerCrossMap).where(PlayerCrossMap.espn_id == espn_id)
        )
        row = result.scalar_one_or_none()
        return row.sleeper_id if row else None
```

### Anti-Patterns to Avoid

- **Storing plaintext credentials in DB:** Always Fernet-encrypt before writing. `credentials_encrypted` column must always be `bytes`, never `str`.
- **Hardcoding Yahoo game key (461):** The game key changes each season. Fetch from Yahoo's `/games;game_codes=nfl` endpoint at runtime and cache it.
- **Assuming ESPN cookies are permanent:** Always handle 401 from ESPN as a credential expiry event, not a generic error.
- **Calling Yahoo API with expired access token:** Cache token `expires_at` in the encrypted credentials blob; proactively refresh 5 minutes before expiry, don't wait for a 401.
- **Single-request ESPN league fetch without views:** Without explicit `?view=` parameters, ESPN returns minimal data. Always specify all needed views in one request to avoid multiple round trips.
- **Adding espn-api or yfpy as dependencies:** These libraries are synchronous (espn-api v0.46) or have their own token storage model (yfpy) that conflicts with the established async pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Yahoo OAuth state + PKCE | Custom state parameter | authlib starlette_client (already installed) | authlib handles CSRF state, code verifier, and redirect automatically |
| Token encryption | Custom AES or XOR cipher | cryptography.Fernet (already transitively installed) | Fernet handles AES-128-CBC + HMAC-SHA256 in one call; hand-rolled ciphers fail MAC verification |
| Yahoo token refresh | Manual HTTP POST to get_token | authlib token refresh utility or hand-roll POST (simple) | The POST is simple enough to hand-roll safely; authlib async refresh is complex to wire up without a session |
| ESPN cookie parsing | Browser-side cookie extraction | User pastes SWID and espn_s2 directly into the form | ESPN's reCAPTCHA prevents programmatic login; paste is the only viable approach |
| Player ID fuzzy matching | Levenshtein or custom phonetics | difflib.SequenceMatcher (stdlib) | stdlib is sufficient for name+team matching; no extra dependency needed |
| Rate limit sliding window | Custom sorted set TTL management | Redis INCR + EXPIRE (atomic fixed window) | Sliding window complexity isn't justified for ~100–200 req/10min budgets |

**Key insight:** The ESPN API is unofficial and subject to change without notice. Build the ESPNClient as a thin stateless wrapper — no business logic inside it. This isolates breakage to one file if ESPN changes endpoints.

---

## Data Model Changes

### New Table: `user_credentials`

Stores encrypted platform credentials per user per platform. One row per (user, platform) pair — a user with two Yahoo leagues has one credential row for Yahoo.

```python
# File: backend/app/models/credential.py
class UserCredential(Base):
    __tablename__ = "user_credentials"
    __table_args__ = (UniqueConstraint("user_id", "platform"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str]              # "yahoo" | "espn"
    credentials_encrypted: Mapped[bytes]  # Fernet-encrypted JSON blob
    is_healthy: Mapped[bool] = mapped_column(default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
```

**Encrypted JSON blob contents:**
- Yahoo: `{"access_token": "...", "refresh_token": "...", "expires_at": 1234567890}`
- ESPN private: `{"swid": "{...}", "espn_s2": "LONG_TOKEN", "is_public": false}`
- ESPN public: `{"league_id": "12345", "is_public": true}` (no sensitive data; still encrypt for consistency)

### New Table: `player_cross_map`

Maps player IDs across platforms. Sleeper ID is the internal canonical key (Sleeper's player pool is already cached and used throughout the system).

```python
# File: backend/app/models/player.py (new)
class PlayerCrossMap(Base):
    __tablename__ = "player_cross_map"

    sleeper_id: Mapped[str] = mapped_column(primary_key=True)
    yahoo_id: Mapped[str | None] = mapped_column(default=None, index=True)
    espn_id: Mapped[str | None] = mapped_column(default=None, index=True)
    full_name: Mapped[str]
    position: Mapped[str | None] = mapped_column(default=None)
    team: Mapped[str | None] = mapped_column(default=None)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC).replace(tzinfo=None))
```

### No Changes Required

- `League`: existing `host_platform`, `host_league_id`, `scoring_rules` (JSONB), `roster_format` (JSONB), `keeper_flag` fields are all sufficient. Platform just changes to "yahoo" or "espn".
- `LeagueMember`: existing `host_team_id` works for Yahoo roster IDs and ESPN team IDs.
- `Team`, `Roster`, `User`: no changes needed.
- `User.envelope_key`: already present and `bytes | None`. Generate on first credential write if `None`.

### New Alembic Migration: `002_phase3_credentials_playermap.py`

```python
# Creates user_credentials and player_cross_map tables
def upgrade():
    op.create_table(
        "user_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "platform"),
    )
    op.create_table(
        "player_cross_map",
        sa.Column("sleeper_id", sa.String(), nullable=False),
        sa.Column("yahoo_id", sa.String(), nullable=True),
        sa.Column("espn_id", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("sleeper_id"),
    )
    op.create_index("ix_player_cross_map_yahoo_id", "player_cross_map", ["yahoo_id"])
    op.create_index("ix_player_cross_map_espn_id", "player_cross_map", ["espn_id"])
```

---

## Yahoo Fantasy API Reference

**Authorization endpoint:** `https://api.login.yahoo.com/oauth2/request_auth` [CITED: developer.yahoo.com/oauth2/guide/flows_authcode/]
**Token endpoint:** `https://api.login.yahoo.com/oauth2/get_token` [CITED: developer.yahoo.com/oauth2/guide/flows_authcode/]
**OAuth scope (read):** `fspt-r` [CITED: multiple sources including pipedream.com community]
**OAuth scope (read+write):** `fspt-w` (needed for TM-16 lineup write — Phase 3 only needs `fspt-r`)
**Access token lifetime:** 3600 seconds (1 hour) [CITED: developer.yahoo.com/oauth2/guide/flows_authcode/]
**Refresh token lifetime:** Not specified in docs; treat as long-lived [ASSUMED]

**Yahoo API base URL:** `https://fantasysports.yahooapis.com/fantasy/v2` [CITED: yahoo-fantasy-node-docs.vercel.app]
**Accept header required:** `Accept: application/json` (default response is XML) [CITED: community sources]

**NFL game key by season** (game_key increments per season):
- 2024: `449` [VERIFIED: websearch]
- 2025: `461` [VERIFIED: websearch — cross-referenced from yfpy issue comments]
- **At runtime:** Fetch game key from `GET /games;game_codes=nfl` — do not hardcode

**League key format:** `{game_key}.l.{league_id}` e.g. `461.l.123456` [CITED: yfpy docs]

**Key endpoints:**
| Endpoint | Data Returned |
|----------|---------------|
| `GET /users;use_login=1/games;game_codes=nfl/leagues` | All NFL leagues for authenticated user |
| `GET /league/{league_key}/settings` | Draft type, scoring type, roster positions, waiver rules |
| `GET /league/{league_key}/settings;out=stat_categories` | Full scoring stat definitions |
| `GET /league/{league_key}/teams` | All teams with names and owner info |
| `GET /team/{team_key}/roster;type=week;week={week}` | Weekly roster with player details |

**Rate limits:** Not officially documented. Yahoo throttles "excessive usage." [LOW CONFIDENCE — ASSUMED: conservative budget of 200 req/10min per user in Redis]

**Token refresh:** POST to `https://api.login.yahoo.com/oauth2/get_token` with:
- `Authorization: Basic base64(client_id:client_secret)`
- Body: `grant_type=refresh_token&refresh_token={stored_token}`
- Returns new access_token AND new refresh_token (rotate the stored one) [CITED: official OAuth docs]

---

## ESPN Fantasy API Reference

**Base URL (current as of April 2024):** `https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl` [CITED: stmorse.github.io/journal/espn-fantasy-v3.html]

> The URL changed from `fantasy.espn.com` to `lm-api-reads.fantasy.espn.com` in April 2024. Using the old URL returns 301 redirects. [CITED]

**League endpoint:** `GET /seasons/{year}/segments/0/leagues/{league_id}` [CITED]

**View parameters** (pass multiple as `?view=X&view=Y`):
| View | Data |
|------|------|
| `mSettings` | League settings, scoring system, roster positions, keeper settings |
| `mRoster` | All team rosters for current week |
| `mTeam` | Team names, records, owners |
| `mMatchupScore` | Current week scores and matchups |
| `mStandings` | Season standings |
| `mDraftDetail` | Draft picks and results |

**Recommended combined call:**
```
GET /seasons/{year}/segments/0/leagues/{league_id}?view=mSettings&view=mRoster&view=mTeam&view=mStandings
```

**Private league authentication:** Pass cookies with every request:
```python
cookies = {"SWID": "{user-swid}", "espn_s2": "long-token-here"}
```
[CITED: espn-api library documentation and stmorse.github.io]

**Public league:** No cookies needed for `mSettings` and `mTeam`; some views may return empty data without auth. [MEDIUM CONFIDENCE — community confirmed but not guaranteed for all views]

**Cookie expiry:** No official documentation. ESPN cookies appear to last months. [LOW CONFIDENCE] Detection: treat any 401/403 response as credential expiry.

**Additional data for specific week:**
- Rosters for a specific week: append `&scoringPeriodId={week}` [CITED: community sources]

**Rate limits:** No documentation for the unofficial API. [LOW CONFIDENCE — ASSUMED: conservative budget of 100 req/10min per user]

**ESPN player ID:** Integer in the range of ~1–5 million (unique per player). Returned in roster data as `playerId` field. [MEDIUM CONFIDENCE]

---

## Player ID Cross-Mapping (MP-08)

### Strategy

Three ID spaces: Sleeper uses string integers (~4 digits), Yahoo uses integers (~5 digits), ESPN uses integers (~5+ digits). They do not overlap.

**Primary source:** dynastyprocess player_ids dataset via nflverse (built weekly, covers fantasy-relevant players) [CITED: nflreadr.nflverse.com]

**Download URL (raw CSV):**
```
https://github.com/dynastyprocess/data/raw/main/player_ids.csv
```
[ASSUMED: needs verification at implementation time; the nflreadr R package sources from dynastyprocess/data]

**Alternative source:** mayscopeland/ffb_ids
```
https://raw.githubusercontent.com/mayscopeland/ffb_ids/main/player_ids.csv
```
[CITED: mayscopeland/ffb_ids GitHub repo — explicitly includes Yahoo, ESPN, Sleeper IDs for 2023-2026 draft-relevant players]

**Relevant columns in ffb_ids CSV:**
- `sleeper_id` — Sleeper player ID
- `yahoo_id` — Yahoo player ID
- `espn_id` — ESPN player ID
- `name` — player name
- `position` — position abbreviation
- Individual defensive players excluded

**Loading strategy:**
1. arq task `seed_player_cross_map()` runs on Phase 3 deploy (Wave 0 equivalent) and weekly thereafter
2. Download CSV via httpx GET to raw URL
3. Bulk upsert into `player_cross_map` table
4. Missing mappings (CSV doesn't cover all players): fallback fuzzy match by `full_name` + `position` using `difflib.SequenceMatcher(ratio > 0.85)`
5. Log unmapped player IDs per import for future manual review

**Coverage expectation:** The ffb_ids CSV covers "players most relevant for 2023-2026 fantasy football drafts." Backup/handcuff players and rookies may be missing. [ASSUMED: fuzzy fallback handles these cases]

---

## Common Pitfalls

### Pitfall 1: Yahoo API Returns XML by Default
**What goes wrong:** GET requests to Yahoo's fantasy API without an Accept header return XML, causing JSON parse failures.
**Why it happens:** Yahoo's API predates JSON-first design; XML is the legacy default.
**How to avoid:** Always set `Accept: application/json` in YahooClient headers.
**Warning signs:** `json.JSONDecodeError` on Yahoo API responses.

### Pitfall 2: Yahoo Access Token Expiry During League Import
**What goes wrong:** A long league import sequence fails mid-way because the access token expires (1-hour lifetime) between API calls.
**Why it happens:** Yahoo access tokens last only 3600 seconds. A user with 5+ Yahoo leagues and many teams could trigger enough API calls to span an hour.
**How to avoid:** (a) Cache `expires_at` in the encrypted credentials; (b) proactively refresh if `expires_at - now < 300s` before any batch operation; (c) handle 401 by refreshing and retrying once.

### Pitfall 3: ESPN Base URL Changes Without Notice
**What goes wrong:** The ESPN API base URL has changed at least twice (fantasy.espn.com → lm-api-reads.fantasy.espn.com). A hardcoded URL breaks silently.
**Why it happens:** ESPN doesn't maintain or document the unofficial API.
**How to avoid:** Store the base URL in settings (ESPNAPI_BASE) rather than hardcoded in ESPNClient; make it easy to update in .env.

### Pitfall 4: Fernet Key Must Be Exactly 32 Bytes → Base64 Encoded
**What goes wrong:** Passing raw bytes to `Fernet()` raises `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`.
**Why it happens:** Fernet expects a base64-encoded key, not raw bytes.
**How to avoid:** Always `base64.urlsafe_b64encode(user.envelope_key)` before constructing Fernet.
**Warning signs:** `ValueError` on first credential encrypt/decrypt attempt.

### Pitfall 5: Yahoo League Key vs League ID
**What goes wrong:** Passing the numeric league ID directly to Yahoo API instead of the compound `{game_key}.l.{league_id}` format returns 404.
**Why it happens:** Yahoo requires the compound key for all league resource calls.
**How to avoid:** Construct league_key from game_key at import time; store both `host_league_id` (numeric, for dedup) and `league_key` (compound, for API calls) — or reconstruct league_key from game_key + host_league_id at call time.

### Pitfall 6: ESPN `mRoster` View Returns All Teams in One Response
**What goes wrong:** Iterating roster data expecting one team's roster from the combined league response, but `mRoster` returns all teams simultaneously.
**Why it happens:** ESPN's API is league-centric; each view key contains the full league dataset.
**How to avoid:** Parse the ESPN response as `response["teams"]` → array of all teams; filter by team ID to find the user's team.

### Pitfall 7: `UserCredential` Platform Scope vs League Scope
**What goes wrong:** Storing credentials per-league instead of per-user-per-platform, causing duplicate encrypt/decrypt and storage bloat.
**Why it happens:** Intuition says "connect a league" but the credentials cover all leagues on that platform.
**How to avoid:** `user_credentials` has UNIQUE(user_id, platform). One Yahoo credential covers all the user's Yahoo leagues. One ESPN credential covers all their ESPN leagues.

### Pitfall 8: ESPN Cookie Expiry Not Signaled by Standard 401
**What goes wrong:** ESPN may return 200 with empty data rather than 401 when cookies are technically present but expired, making expiry detection miss.
**Why it happens:** ESPN's unofficial API has inconsistent error signaling.
**How to avoid:** In addition to catching 401, validate that the response contains expected fields (e.g., `response.get("teams")` is not None and not empty). Treat an empty/malformed 200 as "suspect" and attempt revalidation.

---

## Data Normalization: Yahoo/ESPN → Existing Schema

### League.scoring_rules (JSONB)

The existing `scoring_rules` stores Sleeper's `scoring_settings` dict directly. For Yahoo and ESPN, normalize to a common format:

```python
# Normalized format (all platforms):
{
    "platform_raw": {...},  # original API response for reference
    "normalized": {
        "pass_yd": 0.04,      # points per passing yard
        "pass_td": 4.0,
        "rush_yd": 0.1,
        "rec": 1.0,           # PPR value (0 = standard, 0.5 = half-PPR, 1.0 = PPR)
        # etc.
    },
    "keeper_settings": {
        "max_keepers": 3,
        "keeper_cost_rounds": 1,  # Yahoo: cost in draft rounds
        "keeper_cost_money": None,  # Yahoo auction: cost in dollars
        "contract_years": None,    # Dynasty: contract length
    },
    "unmodeled_rules": ["bonus_pass_yd_400", "custom_rule_xyz"]  # MP-09
}
```

### League.roster_format (JSONB)

```python
# Normalized format (all platforms):
{
    "positions": ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T", "K", "DEF", "BN", "BN", ...]
}
```

Yahoo uses `"FLEX"` instead of Sleeper's `"FLEX"`; ESPN uses `"RB/WR/TE"`. Normalize to Sleeper's convention.

### Keeper Rules (MP-09)

**Yahoo:** `settings.settings.max_keepers`, `settings.settings.keeper_cost_type` (0=none, 1=round), `settings.settings.num_keepers`
**ESPN:** `settings.settings.keeperOrderType`, `settings.settings.keeperCount`, `settings.settings.keeperSeason`
**Unmodeled:** Any field not in the known mapping → append field name to `unmodeled_rules` list with raw value.

---

## Frontend Additions

### MP-06: Global Expired Credential Banner

The banner must appear on every page. It should be driven by a global React state derived from the API.

**Recommended approach:**
1. `GET /api/v1/users/me` (already exists) — extend its response to include `credential_health: [{platform: "yahoo", is_healthy: false}, ...]`
2. Auth store (Zustand) holds `unhealthyPlatforms: string[]`
3. Layout component checks `unhealthyPlatforms.length > 0` and renders a sticky banner
4. Banner text: "Your [Yahoo] connection has expired. [Reconnect]" with a link to `/connect?reconnect=yahoo`

### MP-07: Rate Limit Toast

When the backend returns a custom response indicating a cached value was served due to rate limiting, the frontend shows a toast. Use the existing toast infrastructure from Phase 2.

**Recommended approach:** Return `X-Rate-Limited: true` header (or include in response body as `_cached: true`) when serving a cached value after a rate limit hit. Frontend interceptor in `api.ts` checks this header and fires a toast.

---

## Runtime State Inventory

> Phase 3 introduces new database tables and credential state; this is a greenfield addition, not a rename/refactor.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — user_credentials and player_cross_map tables are new | Run Alembic migration 002 |
| Live service config | Yahoo Developer app registration (external to repo) | Developer must register Yahoo app at developer.yahoo.com and obtain client_id/client_secret |
| OS-registered state | None | — |
| Secrets/env vars | YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET new .env vars needed | Add to .env and docker-compose env section; config.py already has stubs |
| Build artifacts | None | — |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Backend runtime | ✓ | pyproject.toml requires >=3.11 | — |
| authlib | Yahoo OAuth | ✓ | 1.7.2 in pyproject.toml | — |
| cryptography | Fernet encryption | ✓ | 49.0.0 (transitive) | Must add explicit dep |
| httpx | ESPN/Yahoo clients | ✓ | ≥0.27.0 in pyproject.toml | — |
| Redis | Rate limiting | ✓ | docker-compose service | — |
| PostgreSQL | user_credentials table | ✓ | docker-compose service | — |
| Yahoo Developer App | Yahoo OAuth | ✗ | Not yet registered | Must register at developer.yahoo.com before any Yahoo test |
| ESPN unofficial API | ESPN data | ✓ (unofficial) | No version — URL-based | No stable fallback; monitor for URL changes |

**Missing dependencies with no fallback:**
- Yahoo Developer App registration is an external prerequisite that requires human action (visiting developer.yahoo.com, creating an app, obtaining client_id and client_secret).

**Missing dependencies with fallback:**
- `cryptography` is transitively installed but must be added explicitly to `pyproject.toml` to avoid breakage if authlib ever changes its dependency tree.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (already in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_yahoo_client.py tests/test_espn_client.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MP-01 | Yahoo OAuth callback stores encrypted refresh token | unit | `pytest tests/test_credential_service.py::test_yahoo_encrypt_decrypt -x` | ❌ Wave 0 |
| MP-02 | Yahoo league import produces same data shape as Sleeper | unit | `pytest tests/test_league_service.py::test_import_yahoo_league -x` | ❌ Wave 0 |
| MP-03 | ESPN private connect validates cookies, encrypts them | unit | `pytest tests/test_espn_client.py::test_espn_private_connect -x` | ❌ Wave 0 |
| MP-04 | ESPN public connect works without cookies | unit | `pytest tests/test_espn_client.py::test_espn_public_connect -x` | ❌ Wave 0 |
| MP-05 | Expired cookie returns specific error, not 500 | unit | `pytest tests/test_espn_client.py::test_expired_cookies -x` | ❌ Wave 0 |
| MP-06 | Unhealthy credential reflected in /users/me response | unit | `pytest tests/test_auth_service.py::test_credential_health -x` | ❌ Wave 0 |
| MP-07 | Rate limit hit returns cached value and sets header | unit | `pytest tests/test_rate_limit.py::test_yahoo_rate_limit_hit -x` | ❌ Wave 0 |
| MP-08 | Yahoo player_id resolves to sleeper_id via cross_map | unit | `pytest tests/test_player_id_mapper.py::test_yahoo_to_sleeper -x` | ❌ Wave 0 |
| MP-09 | Keeper count extracted from Yahoo league settings | unit | `pytest tests/test_league_service.py::test_yahoo_keeper_extraction -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_yahoo_client.py tests/test_espn_client.py tests/test_credential_service.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_yahoo_client.py` — covers MP-01, MP-02
- [ ] `tests/test_espn_client.py` — covers MP-03, MP-04, MP-05
- [ ] `tests/test_credential_service.py` — covers MP-01, MP-06
- [ ] `tests/test_player_id_mapper.py` — covers MP-08
- [ ] `tests/test_rate_limit.py` — covers MP-07
- [ ] `tests/fixtures/yahoo_league.json` — sample Yahoo API response for unit tests
- [ ] `tests/fixtures/espn_league.json` — sample ESPN API response for unit tests

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Yahoo OAuth via authlib; ESPN uses session cookies (user-provided, not our auth) |
| V3 Session Management | yes | Yahoo refresh tokens stored encrypted; ESPN cookies stored encrypted; never in browser |
| V4 Access Control | yes | Credentials scoped to user_id; league access enforced by existing get_league_for_user dep |
| V5 Input Validation | yes | SWID/espn_s2 validated as non-empty strings; league_id validated as numeric; Pydantic models on all endpoints |
| V6 Cryptography | yes | Fernet (AES-128-CBC + HMAC-SHA256) for credential storage; never store plaintext tokens |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Yahoo OAuth state forgery (CSRF) | Spoofing | authlib handles state parameter automatically |
| Credential theft via DB dump | Information Disclosure | Fernet encryption; envelope_key in users table (different breach vector required) |
| Yahoo refresh token reuse after revocation | Tampering | Treat 401 on refresh as credential invalid; mark is_healthy=False; prompt re-auth |
| ESPN cookie injection (user pastes malicious value) | Tampering | Validate cookies length and charset; test against live ESPN API before storing |
| Rate limit bypass (multiple users sharing credentials) | Elevation | Rate limit keyed by user_id; credentials are per-user |
| Replay attack on OAuth callback | Spoofing | authlib one-time state + code; existing SessionMiddleware |
| SWID/espn_s2 logged in plaintext | Information Disclosure | Never log credential values; log only hashed or truncated versions |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Yahoo rate limit: conservative 200 req/10min per user | Rate limiting | May be higher or lower; adjust in .env if Yahoo starts throttling |
| A2 | ESPN rate limit: conservative 100 req/10min per user | Rate limiting | ESPN may block IPs for bursty requests; monitor and tune |
| A3 | dynastyprocess/data player_ids.csv is at `github.com/dynastyprocess/data/raw/main/player_ids.csv` | Player cross-map | URL may differ; verify at implementation time with a GET request |
| A4 | Yahoo refresh tokens do not expire as long as they are used | Yahoo OAuth | If Yahoo expires inactive refresh tokens, need to re-authenticate; add `last_refreshed_at` to credentials blob |
| A5 | ESPN public leagues expose `mSettings` and `mTeam` views without auth | ESPN API | Some ESPN public leagues may require SWID for certain views; test on a real public league |
| A6 | `User.envelope_key` stores 32 raw bytes (not already base64-encoded) | Credential encryption | If envelope_key is stored as base64 string or in a different format, Fernet construction code must adapt |
| A7 | ESPN cookie lifespan is weeks to months | ESPN expiry | If cookies expire faster (days), must prompt re-auth more frequently |
| A8 | Yahoo game key for NFL 2025 season is 461 | Yahoo API | Verify by calling `/games;game_codes=nfl` at runtime; don't hardcode |
| A9 | fuzzy match threshold 0.85 SequenceMatcher ratio is sufficient for player name matching | Player ID mapper | May produce false positives for similar names (e.g., "Chris Williams" vs "Christian Williams"); add team+position as secondary filter |

---

## Open Questions

1. **Yahoo Developer App Registration**
   - What we know: Yahoo requires a registered developer app with client_id/client_secret; config.py already has empty stubs
   - What's unclear: Whether Yahoo's Fantasy Sports API is still open for new app registrations in 2026 (some reports of approval delays)
   - Recommendation: Register the app before Phase 3 execution begins; this is the single human prerequisite

2. **ESPN Public League Cookie Requirement**
   - What we know: Private leagues need both cookies; community says public leagues work without cookies for basic data
   - What's unclear: Whether `mRoster` view on public leagues returns player names or just IDs without auth
   - Recommendation: Test a known public ESPN league (e.g., a public test league) at Wave 0 before finalizing the public path

3. **Yahoo Write Scope for TM-16**
   - What we know: `fspt-r` is read-only; `fspt-w` is read+write; TM-16 (lineup write) is Phase 2 scope but deferred
   - What's unclear: Whether to request `fspt-w` at Phase 3 OAuth so users don't have to re-authorize later when TM-16 is enabled
   - Recommendation: Request `fspt-w` scope at Phase 3 (plan for the future); the user sees no difference; write routes can remain 501 until Phase 3 enables them

4. **Player ID Map Coverage for Non-ADP Players**
   - What we know: ffb_ids covers "most relevant for 2023-2026 drafts," excludes individual defensive players
   - What's unclear: Coverage for practice squad players, rookies added mid-season, and all DEF/K units
   - Recommendation: Log unmapped player IDs at import time; add a monitoring alert if >10% of roster players are unmapped

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ESPN API at `fantasy.espn.com` | `lm-api-reads.fantasy.espn.com` | April 2024 | Old URL redirects but may break in future; use new URL |
| ESPN API access with username/password | Cookie-based only (SWID + espn_s2) | ~2022 | reCAPTCHA blocks programmatic login; cookie paste is the only viable method |
| Yahoo OAuth 1.0a | Yahoo OAuth 2.0 | 2020 | OAuth 1.0a is deprecated; 2.0 is the required flow |
| yfpy library for Yahoo | Custom YahooClient | N/A | yfpy v17 is synchronous-first and has its own token storage; conflicts with async pattern |
| espn-api library (v0.46 synchronous) | Custom ESPNClient | N/A | espn-api is synchronous; would need thread executor in async FastAPI |

**Deprecated/outdated:**
- Yahoo OAuth 1.0a: fully deprecated; do not use
- ESPN API at `fantasy.espn.com`: functional but returns 301; switch to `lm-api-reads` domain
- ESPN `leagueHistory` argument: ESPN removed historical season access via this parameter (as of August 2025 [CITED: espn-api web search results])

---

## Sources

### Primary (HIGH confidence)
- `developer.yahoo.com/oauth2/guide/flows_authcode/` — Yahoo OAuth 2.0 endpoints, token format, access token lifetime
- `cryptography.io/en/latest/fernet/` — Fernet encryption API and key format
- Existing codebase: `backend/app/core/cache.py`, `backend/app/models/user.py`, `backend/app/services/sleeper_client.py` — verified patterns to mirror

### Secondary (MEDIUM confidence)
- `stmorse.github.io/journal/espn-fantasy-v3.html` — ESPN Fantasy API v3 base URL, view parameters, cookie auth
- `github.com/cwendt94/espn-api` — espn-api library confirms cookie auth mechanics (library inspects actual ESPN API calls)
- `github.com/uberfastman/yfpy` + `yfpy.uberfastman.com/quickstart/` — Yahoo Fantasy API endpoint methods; confirms game key format
- `yahoo-fantasy-node-docs.vercel.app` — Yahoo Fantasy API league settings endpoint URL pattern
- `nflreadr.nflverse.com/articles/dictionary_ff_playerids.html` — confirms Yahoo, ESPN, Sleeper IDs in player ID dataset
- `github.com/mayscopeland/ffb_ids` — confirms ffb_ids CSV includes all three platform IDs; 2023-2026 coverage

### Tertiary (LOW confidence — flag for validation)
- ESPN rate limits: not documented; budgets are conservative estimates only
- Yahoo rate limits: not documented; Yahoo says "excessive usage may be throttled"
- ESPN cookie lifetime: not officially documented
- Yahoo refresh token lifetime: not explicitly documented as permanent

---

## Metadata

**Confidence breakdown:**
- Yahoo OAuth flow: HIGH — endpoints and scope verified from official Yahoo Developer docs
- Yahoo Fantasy API endpoints: MEDIUM — confirmed from community docs and library code
- ESPN cookie auth: HIGH — confirmed by espn-api library (v0.46.0 active) and multiple blog posts
- ESPN base URL: MEDIUM — changed in April 2024; current URL confirmed from multiple 2024-2025 sources
- Rate limits: LOW — both platforms have undocumented limits; budgets are conservative estimates
- Credential encryption: HIGH — Fernet pattern is standard; User.envelope_key already in schema
- Player ID mapping: MEDIUM — dataset existence confirmed; exact column names and coverage assumed from description

**Research date:** 2026-06-28
**Valid until:** 2026-09-01 for ESPN base URL (monitor for changes); 2026-12-31 for Yahoo OAuth; indefinite for encryption and rate-limit patterns
