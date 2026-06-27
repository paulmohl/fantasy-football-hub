# Phase 2: Team Manager Core - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 18 new/modified files
**Analogs found:** 17 / 18

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/app/api/v1/team.py` | router | request-response | `backend/app/api/v1/leagues.py` | exact |
| `backend/app/services/projection_service.py` | service | request-response + cache | `backend/app/services/sleeper_client.py` | role-match |
| `backend/app/services/lineup_optimizer.py` | service | transform | `backend/app/services/league_service.py` | role-match |
| `backend/app/services/waiver_ranker.py` | service | transform | `backend/app/services/league_service.py` | role-match |
| `backend/app/services/trade_evaluator.py` | service | request-response + cache | `backend/app/services/sleeper_client.py` | role-match |
| `backend/app/services/weather_service.py` | service | request-response + cache | `backend/app/services/sleeper_client.py` | role-match |
| `backend/app/data/nfl_stadiums.py` | utility/config | — | none | no analog |
| `frontend/src/pages/TeamPage.tsx` | page (extend) | request-response | self (stub exists) | exact |
| `frontend/src/components/LeagueSwitcher.tsx` | component | event-driven | `frontend/src/components/Layout.tsx` | role-match |
| `frontend/src/components/LineupCard.tsx` | component | request-response | `frontend/src/pages/TeamPage.tsx` (PlayerCard within) | role-match |
| `frontend/src/components/WaiverCard.tsx` | component | request-response | `frontend/src/components/ui/LeagueCard.tsx` | role-match |
| `frontend/src/components/PlayerDetailDrawer.tsx` | component | request-response | `frontend/src/pages/ConnectPage.tsx` (modal pattern) | partial |
| `frontend/src/components/WeatherChip.tsx` | component | transform | `frontend/src/components/ui/FormatBadge.tsx` | role-match |
| `frontend/src/components/TrendChart.tsx` | component | transform | none (Recharts new) | no analog |
| `frontend/src/store/league.ts` | store | event-driven | `frontend/src/store/auth.ts` | exact |
| `backend/tests/test_lineup_optimizer.py` | test | — | `backend/tests/test_leagues.py` | exact |
| `backend/tests/test_waiver_ranker.py` | test | — | `backend/tests/test_leagues.py` | exact |
| `backend/tests/test_weather_service.py` | test | — | `backend/tests/test_leagues.py` | exact |
| `backend/tests/test_team_routes.py` | test | — | `backend/tests/test_auth.py` | exact |

---

## Pattern Assignments

### `backend/app/api/v1/team.py` (router, request-response)

**Analog:** `backend/app/api/v1/leagues.py`

**Imports pattern** (leagues.py lines 1–23):
```python
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey
from app.core.database import get_db
from app.core.deps import get_current_user, get_league_for_user
from app.core.redis import get_redis
from app.models.league import League, LeagueMember, Roster
from app.models.user import User
from app.services.sleeper_client import SleeperClient, get_sleeper_client

router = APIRouter(prefix="/team", tags=["team"])
```

**Auth/guard pattern** — every route must use `get_current_user` and `get_league_for_user` (leagues.py lines 27–53). Note: `get_league_for_user` takes `league_id: UUID` as a path param AND the current user — it JOINs through `league_members` so user A cannot see user B's data (LC-09). Endpoints that need the league context (lineup, waiver, standings, trade) should use `get_league_for_user`; the `/my` endpoint should use `get_current_user` only, then query `LeagueMember` for the active league.

**Route handler pattern** (leagues.py lines 27–53):
```python
@router.get("/mine")
async def get_my_leagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(League, LeagueMember)
        .join(LeagueMember, LeagueMember.league_id == League.id)
        .where(LeagueMember.user_id == current_user.id)
        .order_by(LeagueMember.connected_at.desc())
    )
    rows = result.all()
    return [{"id": str(league.id), ...} for league, member in rows]


@router.get("/{league_id}")
async def get_league(
    league: League = Depends(get_league_for_user),
):
    return {"id": str(league.id), ...}
```

**Cache-aside pattern** (sleeper.py lines 38–59 — use this exact shape for Redis reads in team routes):
```python
cached = await redis.get(CacheKey.some_key())
if cached:
    data = json.loads(cached)
else:
    data = await some_client.fetch()
    await redis.set(CacheKey.some_key(), json.dumps(data), ex=TTL_IN_SECONDS)
```

**Router registration** — add to `backend/app/api/v1/__init__.py`:
```python
from app.api.v1 import auth, health, leagues, oauth, sleeper, team, users
router.include_router(team.router)
```

---

### `backend/app/services/projection_service.py` (service, request-response + cache)

**Analog:** `backend/app/services/sleeper_client.py`

**Class + dependency pattern** (sleeper_client.py lines 26–97):
```python
class ProjectionService:
    """Merges FantasyCalc and Sleeper data for player projection ranking.

    Inject redis — use get_projection_service() in FastAPI.
    """

    def __init__(self, http: httpx.AsyncClient, redis):
        self.http = http
        self.redis = redis

    async def get_fantasycalc_values(self, is_dynasty: bool = False) -> list[dict]:
        ...

    async def get_sleeper_players(self) -> dict[str, dict]:
        ...

    async def build_sleeper_id_index(self, fc_values: list[dict]) -> dict[str, dict]:
        ...


async def get_projection_service(redis=Depends(get_redis)):
    async with httpx.AsyncClient(timeout=15.0) as client:
        yield ProjectionService(client, redis)
```

**Custom exception pattern** (sleeper_client.py lines 15–23):
```python
class FantasyCalcError(Exception):
    """Raised for non-200 FantasyCalc API errors."""

class WeatherServiceError(Exception):
    """Raised for Open-Meteo API errors."""
```

**Logging pattern** (sleeper_client.py line 43):
```python
from app.core.logging import logger
logger.info("fantasycalc.fetch", is_dynasty=is_dynasty)
```

**Cache key additions** — extend `backend/app/core/cache.py` with:
```python
@staticmethod
def fantasycalc_values(is_dynasty: bool) -> str:
    return f"fantasycalc:values:{'dynasty' if is_dynasty else 'redraft'}"

@staticmethod
def sleeper_players_nfl() -> str:
    return "sleeper:players:nfl"

@staticmethod
def sleeper_trending_add() -> str:
    return "sleeper:trending:add"

@staticmethod
def sleeper_stats(season: str, week: int) -> str:
    return f"sleeper:stats:{season}:{week}"

@staticmethod
def open_meteo_weather(team_abbr: str, game_date: str) -> str:
    return f"weather:{team_abbr}:{game_date}"
```

**Cache TTL additions** — add to `CacheTTL`:
```python
FANTASYCALC: int = 86400   # 24 hours
SLEEPER_PLAYERS: int = 86400  # 24 hours
SLEEPER_STATS: int = 3600     # 1 hour
SLEEPER_TRENDING: int = 3600  # 1 hour
OPEN_METEO: int = 21600       # 6 hours (once per game day is sufficient)
```

---

### `backend/app/services/lineup_optimizer.py` (service, transform)

**Analog:** `backend/app/services/league_service.py`

**Pure function module pattern** (league_service.py lines 30–49 — pure functions, no class):
```python
"""Lineup optimizer: greedy slot assignment for fantasy football rosters.

Input: roster player_ids, player lookup dict, FantasyCalc value lookup, roster_positions list.
Output: list of slot assignments with confidence scores.
"""

def build_optimal_lineup(
    roster_player_ids: list[str],
    player_lookup: dict,
    fc_value_lookup: dict,
    roster_positions: list[str],
) -> list[dict]:
    """Greedy descent: fill highest-value non-bench slots first."""
    ...
```

**Pitfall guard pattern** (filter Sleeper empty slot IDs before any lookup):
```python
valid_player_ids = [pid for pid in roster_player_ids if pid and pid != "0"]
```

---

### `backend/app/services/waiver_ranker.py` (service, transform)

**Analog:** `backend/app/services/league_service.py` (pure functions pattern)

Same pure function module pattern as lineup_optimizer. No class needed. Two exported functions: `score_waiver_player(...)` returning `{trend_score, composite_score}` and `rank_waiver_wire(available_player_ids, ...)` returning sorted list with both scores.

---

### `backend/app/services/trade_evaluator.py` (service, request-response + cache)

**Analog:** `backend/app/services/sleeper_client.py` (class + dependency injection)

Thin wrapper over `ProjectionService.get_fantasycalc_values()`. Exposes `compare_players(player_id_a, player_id_b, fc_index)` returning recommendation, value delta, confidence, and three biggest factors (tier gap, trend30Day, injury_status, positional need). Can be a standalone module with functions rather than a class since it delegates caching to ProjectionService.

---

### `backend/app/services/weather_service.py` (service, request-response + cache)

**Analog:** `backend/app/services/sleeper_client.py` (class + async HTTP client)

```python
class WeatherService:
    def __init__(self, http: httpx.AsyncClient, redis):
        self.http = http
        self.redis = redis

    async def get_game_weather(self, team_abbr: str, game_date: str) -> dict | None:
        from app.data.nfl_stadiums import NFL_STADIUMS
        stadium = NFL_STADIUMS.get(team_abbr)
        if not stadium or stadium["indoor"]:
            return None
        key = CacheKey.open_meteo_weather(team_abbr, game_date)
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        async with self.http as client:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": stadium["lat"],
                "longitude": stadium["lon"],
                "hourly": "wind_speed_10m,precipitation,weather_code,snowfall",
                "wind_speed_unit": "mph",  # CRITICAL: always specify mph (Pitfall 5)
                "forecast_days": 7,
            })
            r.raise_for_status()
        data = _extract_kickoff_weather(r.json(), game_date)
        await self.redis.set(key, json.dumps(data), ex=CacheTTL.OPEN_METEO)
        return data


async def get_weather_service(redis=Depends(get_redis)):
    async with httpx.AsyncClient(timeout=15.0) as client:
        yield WeatherService(client, redis)
```

---

### `backend/app/data/nfl_stadiums.py` (utility/config, static data)

**Analog:** None — no static data module exists yet. Closest pattern is `backend/app/core/cache.py` (pure module, no class, only data + constants).

```python
"""Static NFL stadium lookup: {team_abbr: {lat, lon, indoor, name}}.

Update if a team relocates or opens a new stadium.
9 indoor/dome stadiums: LV, LAR, LAC, IND, DET, MIN, ATL, ARI, HOU
"""

NFL_STADIUMS: dict[str, dict] = {
    "KC":  {"lat": 39.0490,  "lon": -94.4839,  "indoor": False, "name": "Arrowhead"},
    "BUF": {"lat": 42.7738,  "lon": -78.7870,  "indoor": False, "name": "Highmark"},
    "LV":  {"lat": 36.0909,  "lon": -115.1833, "indoor": True,  "name": "Allegiant"},
    # ... all 32 teams
}

WEATHER_WIND_THRESHOLD_MPH = 20
```

---

### `frontend/src/pages/TeamPage.tsx` (page, extend existing stub)

**Analog:** Self — the stub already exists at `frontend/src/pages/TeamPage.tsx` (lines 1–108).

**Existing patterns to keep** (TeamPage.tsx lines 1–108):
- `useQuery<TeamData>` from `@tanstack/react-query` — keep this; extend `queryKey` to include `activeLeagueId` from the new `useLeagueStore`
- `api.get('/team/my')` from `@/lib/api` — existing axios instance, keep
- `PlayerCard` inner component (lines 36–63) — extend with `onClick` to open `PlayerDetailDrawer`; add draggable wrapper for dnd-kit
- Loading spinner pattern (lines 71–76) — reuse across all new cards
- Error/empty state pattern (lines 78–85) — reuse

**Change to query key** (critical for Pitfall 6 — league switch cache invalidation):
```typescript
const { activeLeagueId } = useLeagueStore()

const { data } = useQuery<TeamData>({
  queryKey: ['my-team', activeLeagueId],   // include leagueId so cache invalidates on switch
  queryFn: () => api.get('/team/my').then((r) => r.data),
  enabled: !!activeLeagueId,
})
```

**Page layout extension** — extend the `return` block to stack new card components:
```typescript
return (
  <div className="px-4 pt-10 pb-4 space-y-4">
    <LeagueSwitcher />
    <LineupCard leagueId={activeLeagueId} />
    <WaiverCard leagueId={activeLeagueId} />
    {selectedPlayer && (
      <PlayerDetailDrawer player={selectedPlayer} onClose={() => setSelectedPlayer(null)} />
    )}
  </div>
)
```

---

### `frontend/src/components/LeagueSwitcher.tsx` (component, event-driven)

**Analog:** `frontend/src/components/Layout.tsx` (nav element) + `frontend/src/components/ui/LeagueCard.tsx` (league item display)

**Nav integration pattern** (Layout.tsx lines 1–59) — LeagueSwitcher sits above or within the `<main>` scroll area, not inside `<nav>`. It reads `useLeagueStore` (new) and `useAuthStore` (existing).

**League item display pattern** (LeagueCard.tsx lines 19–53) — button with `cn()` for selected state, `FormatBadge` for league type:
```typescript
import { cn } from '@/lib/utils'
import { useLeagueStore } from '@/store/league'

export function LeagueSwitcher() {
  const { activeLeagueId, setActiveLeague } = useLeagueStore()
  const { data: leagues } = useQuery({
    queryKey: ['leagues/mine'],
    queryFn: () => api.get('/leagues/mine').then((r) => r.data),
  })

  if (!leagues || leagues.length <= 1) return null  // hide if only one league

  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {leagues.map((league) => (
        <button
          key={league.id}
          onClick={() => setActiveLeague(league.id)}
          className={cn(
            'shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors',
            activeLeagueId === league.id
              ? 'border-accent bg-[#0e1a2e] text-accent'
              : 'border-border text-muted hover:border-accent/50',
          )}
        >
          {league.name} · {league.season}
        </button>
      ))}
    </div>
  )
}
```

---

### `frontend/src/components/LineupCard.tsx` (component, request-response)

**Analog:** `frontend/src/pages/TeamPage.tsx` — specifically the `PlayerCard` component (lines 36–63) and query pattern (lines 66–69).

**Query pattern** (TeamPage.tsx lines 66–69 — extend with leagueId in key):
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['team-lineup', leagueId],
  queryFn: () => api.get('/team/lineup').then((r) => r.data),
  enabled: !!leagueId,
})
```

**PlayerCard base** (TeamPage.tsx lines 36–63) — wrap with dnd-kit `useSortable`:
```typescript
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function DraggablePlayerCard({ slot }: { slot: RosterSlot }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: slot.slot_type,
  })
  const style = { transform: CSS.Transform.toString(transform), transition }
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <PlayerCard slot={slot} />
    </div>
  )
}
```

**Side-by-side layout** — use CSS grid `grid-cols-2` with current lineup on left and optimal on right. Current lineup comes from `data.current_roster`; optimal from `data.optimal_roster`.

---

### `frontend/src/components/WaiverCard.tsx` (component, request-response)

**Analog:** `frontend/src/components/ui/LeagueCard.tsx` (list item pattern) + TeamPage.tsx (query pattern)

**Query + toggle pattern:**
```typescript
const [mode, setMode] = useState<'trend' | 'composite'>('composite')

const { data } = useQuery({
  queryKey: ['team-waiver', leagueId, mode],
  queryFn: () => api.get(`/team/waiver?mode=${mode}`).then((r) => r.data),
  enabled: !!leagueId,
})
```

**Dropdown pattern** — use `@radix-ui/react-dropdown-menu` (already installed). Import from `@radix-ui/react-dropdown-menu`.

**Item display** — copy `LeagueCard` button structure (LeagueCard.tsx lines 19–53) replacing league fields with player name, position, team, trend_score/composite_score.

---

### `frontend/src/components/PlayerDetailDrawer.tsx` (component, request-response)

**Analog:** `@radix-ui/react-dialog` (already installed). No existing Radix Dialog usage found in codebase — this is the first. Follow Radix Dialog pattern from docs; the closest structural analog is `ConnectPage.tsx` which uses modal-style overlays.

**Radix Dialog shell:**
```typescript
import * as Dialog from '@radix-ui/react-dialog'

export function PlayerDetailDrawer({ player, onClose }: Props) {
  return (
    <Dialog.Root open={!!player} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed bottom-0 left-0 right-0 bg-surface rounded-t-2xl z-50 p-4 max-h-[85vh] overflow-y-auto">
          <Dialog.Title className="text-lg font-bold text-text">{player.full_name}</Dialog.Title>
          {/* WeatherChip, InjuryBadge, TrendChart go here */}
          <Dialog.Close asChild>
            <button className="absolute top-4 right-4 text-muted">✕</button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

**Tailwind class conventions** — copy from TeamPage.tsx: `bg-surface`, `border-border`, `text-text`, `text-muted`, `text-accent`, `rounded-xl`.

---

### `frontend/src/components/WeatherChip.tsx` (component, transform)

**Analog:** `frontend/src/components/ui/FormatBadge.tsx` (pure display component, conditional render by prop)

**Pattern** (FormatBadge.tsx lines 1–27 — same shape: props-in, badge-out):
```typescript
interface WeatherChipProps {
  wind_mph: number
  precipitation_mm: number
  weather_code: number
  is_indoor: boolean
}

export function WeatherChip({ wind_mph, precipitation_mm, weather_code, is_indoor }: WeatherChipProps) {
  if (is_indoor) return null
  const hasWind = wind_mph >= 20
  const hasRain = precipitation_mm > 2.5
  const hasSnow = weather_code >= 71 && weather_code <= 77  // WMO snow codes

  if (!hasWind && !hasRain && !hasSnow) return null

  return (
    <span className="text-xs font-semibold bg-[#1a2020] text-warning px-2 py-0.5 rounded flex items-center gap-1">
      {hasWind && `💨 ${wind_mph}mph`}
      {hasRain && '🌧'}
      {hasSnow && '❄️'}
    </span>
  )
}
```

---

### `frontend/src/components/TrendChart.tsx` (component, transform)

**Analog:** None — first Recharts component in project. Pattern comes from RESEARCH.md Pattern 6 (cited from recharts.org docs). Follow that directly:

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface WeeklyPoint { week: number; pts: number }

export function TrendChart({ data }: { data: WeeklyPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
        <XAxis dataKey="week" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v: number) => [`${v.toFixed(1)} pts`, 'Points']} />
        <Line type="monotone" dataKey="pts" stroke="#6366f1" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

The `#6366f1` stroke matches the existing `text-accent` color in the project (indigo).

---

### `frontend/src/store/league.ts` (store, event-driven)

**Analog:** `frontend/src/store/auth.ts` — exact same Zustand + persist pattern.

**Full pattern to copy and extend** (auth.ts lines 1–25):
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LeagueState {
  activeLeagueId: string | null
  weekOverrides: Record<number, Record<string, string>>  // week -> {slot_type -> player_id}
  setActiveLeague: (id: string) => void
  setOverride: (week: number, slot: string, playerId: string) => void
  clearOverrides: (week: number) => void
}

export const useLeagueStore = create<LeagueState>()(
  persist(
    (set) => ({
      activeLeagueId: null,
      weekOverrides: {},
      setActiveLeague: (id) => set({ activeLeagueId: id }),
      setOverride: (week, slot, playerId) =>
        set((s) => ({
          weekOverrides: {
            ...s.weekOverrides,
            [week]: { ...(s.weekOverrides[week] || {}), [slot]: playerId },
          },
        })),
      clearOverrides: (week) =>
        set((s) => {
          const { [week]: _, ...rest } = s.weekOverrides
          return { weekOverrides: rest }
        }),
    }),
    { name: 'ffhub-league' },  // localStorage key — differs from 'ffhub-auth'
  ),
)
```

---

### `backend/tests/test_lineup_optimizer.py` (test, unit)

**Analog:** `backend/tests/test_leagues.py`

**Unit test pattern** (test_leagues.py lines 1–98):
```python
"""Tests for LineupOptimizer (TM-01, TM-04)."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.lineup_optimizer import build_optimal_lineup


def make_player(player_id: str, positions: list[str], value: int, injury: str | None = None) -> dict:
    return {
        "player_id": player_id,
        "fantasy_positions": positions,
        "injury_status": injury,
        "search_rank": 100,
    }


def make_fc_entry(player_id: str, value: int) -> dict:
    return {"player": {"sleeperId": player_id}, "value": value}


@pytest.mark.asyncio
async def test_optimal_lineup_assigns_starters():
    """TM-01: Standard roster fills all starter slots."""
    ...


@pytest.mark.asyncio
async def test_injured_player_excluded():
    """TM-01/TM-04: OUT player is downweighted and replacement suggested."""
    ...
```

**Key test pattern** — use `@pytest.mark.asyncio` even for pure sync functions (the project's conftest uses asyncio scope). Use `MagicMock(spec=ClassName)` + `AsyncMock` for any async service dependencies.

---

### `backend/tests/test_waiver_ranker.py` (test, unit)

**Analog:** `backend/tests/test_leagues.py` — same pure unit test structure with no async_client fixture (no HTTP needed for service-layer tests).

---

### `backend/tests/test_weather_service.py` (test, unit)

**Analog:** `backend/tests/test_leagues.py`

Key test cases per RESEARCH.md Validation Architecture: `test_indoor_no_chip` (returns None for indoor stadiums), `test_wind_threshold` (≥20 mph returns chip, <20 does not).

Use `mock_redis` fixture from conftest.py (already defined). Mock `httpx.AsyncClient` via `AsyncMock` on `client.get`.

---

### `backend/tests/test_team_routes.py` (test, integration)

**Analog:** `backend/tests/test_auth.py`

**Integration test pattern** (test_auth.py lines 1–48) — uses `async_client` fixture which overrides DB and Redis:
```python
"""Tests for /api/v1/team/* routes (integration)."""
import pytest

@pytest.mark.asyncio
async def test_get_my_team_returns_200(async_client, test_db):
    """Route: /team/my — returns team data for authenticated user."""
    # 1. Create user + league + member rows in test_db
    # 2. Log in to get JWT
    # 3. GET /api/v1/team/my with Authorization header
    # 4. Assert 200 + expected fields
    ...

@pytest.mark.asyncio
async def test_team_isolation(async_client, test_db):
    """LC-09 carryover: /team/* returns 404 for wrong user's league."""
    ...
```

**Auth header pattern** (from test_auth.py lines 52–80):
```python
reg = await async_client.post("/api/v1/auth/register", json={"email": "x@x.com", "password": "password123"})
# manually flip is_verified in test_db, then login for token
login = await async_client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "password123"})
token = login.json()["access_token"]
response = await async_client.get("/api/v1/team/my", headers={"Authorization": f"Bearer {token}"})
```

---

### `backend/tests/fixtures/fc_values_sample.json` and `sleeper_players_sample.json`

No analog — new fixture files. Structure must match verified API response shapes from RESEARCH.md Code Examples section. `fc_values_sample.json` should contain 20 player entries matching the FantasyCalc shape (with `player.sleeperId` field). `sleeper_players_sample.json` should contain 10 player entries keyed by player_id matching the Sleeper `/v1/players/nfl` shape.

---

## Shared Patterns

### Authentication Guard
**Source:** `backend/app/core/deps.py` lines 17–56
**Apply to:** All five `/api/v1/team/*` route handlers

Every team route must declare either `current_user: User = Depends(get_current_user)` (for `/my`) or `league: League = Depends(get_league_for_user)` (for `/lineup`, `/waiver`, `/standings`, `/trade`). `get_league_for_user` implicitly includes auth — do not double-declare `get_current_user` when using `get_league_for_user`.

```python
# Pattern A: user-scoped (GET /team/my)
async def get_my_team(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):

# Pattern B: league-scoped with isolation (GET /team/lineup, /waiver, /standings, /trade)
async def get_lineup(
    league: League = Depends(get_league_for_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    sleeper: SleeperClient = Depends(get_sleeper_client),
):
```

### Redis Cache-Aside
**Source:** `backend/app/api/v1/sleeper.py` lines 38–59 and `backend/app/core/cache.py`
**Apply to:** All backend service methods that call external APIs (FantasyCalc, Sleeper players, Open-Meteo)

```python
key = CacheKey.some_key(param)
cached = await redis.get(key)
if cached:
    return json.loads(cached)
data = await external_call()
await redis.set(key, json.dumps(data), ex=TTL)
return data
```

TTL constants: FantasyCalc = 86400s, Sleeper players = 86400s, Sleeper trending/stats = 3600s, Open-Meteo = 21600s.

### Structured Logging
**Source:** `backend/app/services/sleeper_client.py` line 43; `backend/app/services/league_service.py` line 68
**Apply to:** All service methods

```python
from app.core.logging import logger
logger.info("service.operation.start", player_id=pid, league_id=str(league_id))
```

### React Query Data Fetching (Frontend)
**Source:** `frontend/src/pages/TeamPage.tsx` lines 66–69
**Apply to:** All new card components (LineupCard, WaiverCard, PlayerDetailDrawer data fetch)

```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'

const { activeLeagueId } = useLeagueStore()

const { data, isLoading, error } = useQuery({
  queryKey: ['query-name', activeLeagueId],  // ALWAYS include activeLeagueId (Pitfall 6)
  queryFn: () => api.get('/team/endpoint').then((r) => r.data),
  enabled: !!activeLeagueId,
})
```

### Tailwind Component Conventions
**Source:** `frontend/src/pages/TeamPage.tsx` lines 36–63
**Apply to:** All new frontend components

Standard class tokens used in the project:
- Container: `bg-surface border border-border rounded-xl p-3`
- Raised element: `bg-raised`
- Primary text: `text-text`
- Secondary/label text: `text-muted`
- Accent/highlight: `text-accent`
- Status colors: `bg-danger` (Out), `bg-warning` (Questionable), `bg-success`
- Spacing: `space-y-2` for stacked lists, `gap-3` for flex rows

### NFL State Fetch (Never Hardcode Season)
**Source:** `backend/app/api/v1/leagues.py` lines 82–89 (refresh endpoint)
**Apply to:** Any backend service needing current season or week

```python
cached_state = await redis.get(CacheKey.nfl_state())
if cached_state:
    nfl_state = json.loads(cached_state)
else:
    nfl_state = await sleeper.get_nfl_state()
    await redis.set(CacheKey.nfl_state(), json.dumps(nfl_state), ex=CacheTTL.NFL_STATE)
season = nfl_state["season"]
week = int(nfl_state.get("week", 1))
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/data/nfl_stadiums.py` | config/static | — | No static data module exists in the project yet. Pattern: plain Python module with a dict constant and a few named constants. Follow `backend/app/core/cache.py` structure (module-level, no class). |
| `frontend/src/components/TrendChart.tsx` | component | transform | No chart components exist. Use Recharts pattern from RESEARCH.md Pattern 6 directly. |

---

## Metadata

**Analog search scope:** `backend/app/api/v1/`, `backend/app/services/`, `backend/app/core/`, `backend/tests/`, `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/store/`
**Files read:** 18 source files
**Pattern extraction date:** 2026-06-26
