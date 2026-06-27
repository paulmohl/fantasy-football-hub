# Phase 2: Team Manager Core - Research

**Researched:** 2026-06-26
**Domain:** Fantasy football data services, lineup optimization, waiver wire scoring, weather APIs, drag-and-drop UI, charting
**Confidence:** HIGH (core stack verified via live API calls; some algorithm design is ASSUMED)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **DECISION-001 (Projection Data Source):** Dual source — Sleeper API (weekly/injury data, stats, trending) + FantasyCalc API (dynasty/trade values). No true point projections; optimizer ranks relative value.
- **DECISION-002 (UI Layout):** Card-based vertical stack — lineup optimizer card, waiver wire card, player detail panel, standings/recap card.
- **DECISION-003 (Waiver Wire Formula):** Two user-selectable modes: trend-weighted and full composite. Backend computes both, frontend toggles.
- **DECISION-004 (League Switcher):** Persistent switcher in top nav/sidebar. Zustand store, persisted to localStorage. All Team Manager data re-fetches on switch.
- **No new DB models** for Phase 2 MVP. Reads from existing Roster, Team, League, LeagueMember tables.
- **New backend services (not DB-persisted):** ProjectionService, LineupOptimizer, WaiverRanker, TradeEvaluator.
- **New routes:** `/api/v1/team/my`, `/api/v1/team/lineup`, `/api/v1/team/waiver`, `/api/v1/team/standings`, `/api/v1/team/trade`
- **Cache:** FantasyCalc 24h TTL, Sleeper injury/status 1h TTL.
- **FantasyCalc endpoints:** `GET /values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1` (redraft), `isDynasty=true` (dynasty), `/rankings/current` (rankings — NOT YET CONFIRMED LIVE).

### Claude's Discretion

- Implementation details of ProjectionService, LineupOptimizer, WaiverRanker internals
- Weather data source selection (Open-Meteo confirmed as best free fit)
- Chart library selection (Recharts recommended)
- Drag library selection (dnd-kit recommended)
- FAAB bid formula design
- Confidence score calculation approach
- Test infrastructure additions

### Deferred Ideas (OUT OF SCOPE)

- Writing lineup changes back to Sleeper (Phase 3+)
- Yahoo and ESPN data sources for projections (Phase 3)
- AI natural-language trade summaries (Phase 7)
- Push notifications for waiver wire pickups or lineup alerts (Phase 8)
- User preference persistence to DB (Phase 8)
- TM-16 (Apply suggested lineup via host API) — requires Yahoo/ESPN write scope (Phase 3+)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TM-01 | Optimal starting lineup maximizing projected points within eligibility constraints; each starter shows confidence (0–100) and projected point total | LineupOptimizer: positional slot matching against roster_format JSONB + FantasyCalc `value` + Sleeper `search_rank`. No true projections — use ADP-rank proxy. |
| TM-02 | Current vs optimal lineup side-by-side; "Swap suggested" badge and projected point delta | Frontend: current starters from Roster.snapshot + optimizer result side-by-side card layout |
| TM-03 | Per-player detail panel: projected points, confidence, matchup grade, weather, injury status, opponent rank vs position, recent usage trend, one-paragraph natural-language explanation | Backend aggregates: Sleeper player + stats + FantasyCalc value + Open-Meteo weather; NL explanation is template-based (no LLM in Phase 2) |
| TM-04 | Real-time injury status: OUT shown in red; optimizer auto-suggests replacement | Sleeper `injury_status` field (Active/Questionable/Doubtful/Out/Suspended/IR/PUP/NA). Refresh TTL 1h. |
| TM-05 | Waiver wire ranks all available players by composite score weighted by positional need; re-rankable by raw projection, ownership trend, or breakout score; 30+ targets | WaiverRanker uses Sleeper trending data (`/players/nfl/trending/add`) + FantasyCalc value; available = players not in any team's `starters` or `players` arrays |
| TM-06 | Add dialog suggests 1–3 drop candidates ranked by lowest rest-of-season value; no in-progress players | FantasyCalc `value` as ROS proxy; Sleeper `status` field for in-progress detection |
| TM-07 | Detect waiver type from league settings; FAAB vs rolling priority UI | League `scoring_rules` JSONB from Phase 1 contains `waiver_type` and `waiver_budget`; Sleeper field: `settings.waiver_type` (0=rolling, 2=FAAB) |
| TM-08 | Head-to-head player comparison: recommendation, point delta, confidence, three biggest factors | TradeEvaluator: compare two FantasyCalc `value` entries; diff factors = tier gap, trend30Day, injury_status, positional need |
| TM-09 | Weather chip for 20+ mph wind/heavy rain/snow; projection adjusted down; indoor stadiums never show weather | Open-Meteo `/v1/forecast` + hardcoded NFL stadium lat/lon + indoor flag lookup table |
| TM-10 | "No strong call" banner if all flex options below confidence 55 | Frontend condition: if max(flex_confidence) < 55 render banner instead of top recommendation |
| TM-11 | "Positive game script" factor for RB on team favored 10+ points | Sleeper matchup data provides team spreads (if available); otherwise ASSUMED from external odds source |
| TM-12 | FAAB bid recommendation with confidence range (e.g., $14 ± $3) for FAAB leagues | Formula: player_value_percentile × remaining_budget × positional_scarcity_factor; range from maybeMovingStandardDeviation |
| TM-13 | Per-player season trend chart: weekly pts current season, season totals last 3 seasons, "vs this opponent" toggle | Recharts LineChart + Sleeper `/v1/stats/nfl/regular/{season}/{week}` per-week data |
| TM-14 | Player news feed most-recent-first with source, timestamp, impact tag | Sleeper does NOT provide news; requires third-party news source (RotoBaller API, RotoWire RSS, or curated news) — OPEN QUESTION |
| TM-15 | Drag player into different slot; recomputes projected total + confidence; override remembered for week | dnd-kit `@dnd-kit/sortable` + Zustand store for override state (localStorage, Phase 8 migrates to DB) |
| TM-16 | Yahoo/ESPN write-scope "Apply suggested lineup" (V1 marker) | OUT OF SCOPE for Phase 2 — Phase 3+ |
</phase_requirements>

---

## Summary

Phase 2 builds the data aggregation and UI layer for lineup optimization, waiver wire ranking, and player analysis. The stack relies on two external data sources already validated: Sleeper's public REST API (free, no auth, well-documented) and FantasyCalc's `/values/current` endpoint (free, no auth required, CORS open, confirmed live). No true weekly point projections are available from either source — the optimizer ranks relative value using FantasyCalc `value` scores and Sleeper `search_rank`/`depth_chart_order` as proxies, which is the locked decision from CONTEXT.md.

Sleeper unexpectedly does provide historical stats (`/v1/stats/nfl/regular/{season}/{week}`) and a projections endpoint — however the projections endpoint returns empty objects during the off-season (2026). During the season it may populate, but this cannot be confirmed until the season starts. The stats endpoint works reliably for prior seasons and will be the data source for TM-13 trend charts. Weather data is sourced from Open-Meteo (free, no API key, CORS-unrestricted), queried by NFL stadium latitude/longitude with an indoor-stadium exclusion list baked in as static data.

The two main frontend additions — drag-and-drop lineup overrides (TM-15) and trend charts (TM-13) — require two new npm packages: `@dnd-kit/core` + `@dnd-kit/sortable` (TypeScript, actively maintained, touch-pointer-event support planned for Phase 8) and `recharts` (SVG-based, React-native, 3.6M weekly downloads). Neither conflicts with the existing dependency tree. TM-14 (player news feed) has a data source gap: Sleeper has no news endpoint. This is the only requirement with an unresolved external dependency.

**Primary recommendation:** Implement ProjectionService and WaiverRanker as pure Python service classes (no new DB models), call FantasyCalc once per 24h from a Redis-cached arq worker or on-demand cache-aside, and build all five `/api/v1/team/*` routes in a new `team.py` router. Add `@dnd-kit/sortable` and `recharts` to the frontend.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Lineup optimization | API / Backend (ProjectionService + LineupOptimizer) | — | Ranking logic must be consistent across sessions; not safe to run client-side where users could inspect weights |
| Player injury status | API / Backend (cache layer) | Browser (display) | Sleeper data is fetched server-side; 1h Redis TTL protects rate limits |
| Waiver wire ranking | API / Backend (WaiverRanker) | — | Composite scoring uses server-side state (positional need, FAAB budget) |
| Trade value lookup | API / Backend (TradeEvaluator wrapping FantasyCalc cache) | — | FantasyCalc is a 24h-cached backend call; frontend never hits FantasyCalc directly |
| Weather data | API / Backend (Open-Meteo proxy) | — | Stadium coordinates + indoor flag table lives in backend; frontend just renders chip |
| Drag-to-override state | Browser (Zustand + localStorage) | — | Week override is local user preference; no server persistence in Phase 2 |
| Trend charts | Browser (Recharts) | — | SVG rendering; data pre-aggregated by backend |
| League switcher context | Browser (Zustand persisted) | — | Active league ID is UI state, not server state |
| Player news feed (TM-14) | API / Backend (proxy to third-party) | — | News source TBD; backend fetches and normalizes format |

---

## Standard Stack

### Core (new additions for Phase 2)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@dnd-kit/core` | 6.3.1 [VERIFIED: npm registry] | Drag-and-drop context provider | Actively maintained TypeScript-first successor to deprecated `react-beautiful-dnd`; no React version lock-in |
| `@dnd-kit/sortable` | 10.0.0 [VERIFIED: npm registry] | Sortable list preset for dnd-kit | Ships with `arrayMove()` and `useSortable` hook; handles keyboard + pointer events |
| `recharts` | 3.9.0 [VERIFIED: npm registry] | React SVG chart library | 3.6M weekly downloads; React-native API (no D3 knowledge required); tree-shakes well |

### Supporting (already in project, used in Phase 2)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `zustand` | ^4.5.2 [VERIFIED: package.json] | League switcher + lineup override state | Active league ID + week override map stored with `persist` middleware |
| `@tanstack/react-query` | ^5.45.0 [VERIFIED: package.json] | API data fetching with cache | All five `/api/v1/team/*` routes fetched via `useQuery`; `invalidateQueries` on league switch |
| `@radix-ui/react-dialog` | ^1.1.1 [VERIFIED: package.json] | Player detail panel slide-in drawer | Already installed; use for TM-03 detail panel |
| `@radix-ui/react-dropdown-menu` | ^2.1.1 [VERIFIED: package.json] | Waiver sort mode selector | Already installed; use for TM-05 re-rank dropdown |
| `httpx` | ^0.27.0 [VERIFIED: pyproject.toml] | Async HTTP client for FantasyCalc + Open-Meteo | Already installed from Phase 1 (SleeperClient uses it) |
| `arq` | ^0.26.0 [VERIFIED: pyproject.toml] | Background worker for cache warm-up | Already installed; add FantasyCalc pre-fetch worker |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `recharts` | `chart.js` + `react-chartjs-2` | Canvas-based (no SVG); harder to style with Tailwind; more config boilerplate |
| `@dnd-kit/core` | `@hello-pangea/dnd` (react-beautiful-dnd fork) | Easier for pure list reorder but less flexible for cross-zone (lineup slot → bench) drag |
| Open-Meteo | WeatherAPI.com | Requires API key; rate limits; Open-Meteo is fully free with no key |
| FantasyCalc `/values/current` | FantasyData premium API | $$ cost; not needed given FantasyCalc provides trade values for free |

**Installation (frontend):**
```bash
npm install @dnd-kit/core @dnd-kit/sortable recharts
```

**Version verification:** Verified 2026-06-26 via `npm view`:
- `@dnd-kit/core`: 6.3.1
- `@dnd-kit/sortable`: 10.0.0
- `recharts`: 3.9.0

---

## Architecture Patterns

### System Architecture Diagram

```
Browser
  TeamPage.tsx
    ├── LeagueSwitcher (Zustand activeLeagueId)
    ├── LineupOptimizerCard
    │     ├── GET /api/v1/team/lineup
    │     ├── CurrentLineup + OptimalLineup side-by-side
    │     └── PlayerCard (draggable via dnd-kit) → override stored in Zustand
    ├── WaiverWireCard
    │     ├── GET /api/v1/team/waiver
    │     └── mode toggle: trend-weighted | composite
    ├── PlayerDetailDrawer (Radix Dialog)
    │     ├── projected_points, confidence, matchup_grade
    │     ├── WeatherChip (wind/rain/snow from backend)
    │     ├── InjuryBadge (Sleeper injury_status)
    │     └── TrendChart (Recharts LineChart, Sleeper /stats data)
    └── StandingsCard
          └── GET /api/v1/team/standings

FastAPI Backend (/api/v1/team/*)
  ├── team.py router
  │     ├── GET /my       → LeagueMember → Team → Roster.snapshot
  │     ├── GET /lineup   → ProjectionService → LineupOptimizer → ranked slots
  │     ├── GET /waiver   → WaiverRanker (trend-weighted + composite)
  │     ├── GET /standings → Sleeper /league/{id}/matchups aggregation
  │     └── GET /trade    → TradeEvaluator (FantasyCalc values)
  │
  ├── ProjectionService
  │     ├── fetch_fantasycalc_values() → Redis cache (24h TTL)
  │     └── fetch_sleeper_players()   → Redis cache (1h TTL)
  │
  ├── LineupOptimizer
  │     ├── Input: roster player_ids + position eligibility + FantasyCalc values
  │     └── Output: optimal slot assignments + confidence scores
  │
  ├── WaiverRanker
  │     ├── Input: league roster snapshots + Sleeper trending + FantasyCalc values
  │     └── Output: {trend_score, composite_score} per available player
  │
  └── WeatherService
        ├── Input: week's games (Sleeper matchups → team abbreviation → stadium)
        └── Output: {wind_mph, precipitation_mm, weather_code, is_indoor} per team

External APIs
  ├── Sleeper API (public, no auth)
  │     ├── /v1/players/nfl             → 5MB player dict, cache 24h
  │     ├── /v1/players/nfl/trending/add → add/drop counts, cache 1h
  │     ├── /v1/stats/nfl/regular/{season}/{week} → actual stats per player
  │     ├── /v1/league/{id}/matchups/{week}        → matchup + points data
  │     └── /v1/state/nfl              → current season + week
  │
  ├── FantasyCalc API (public, CORS *, no auth)
  │     └── /values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1
  │           → 200 players, value + rank + trend30Day + maybeTier
  │
  └── Open-Meteo API (public, no key, CORS *)
        └── /v1/forecast?latitude={lat}&longitude={lon}&hourly=wind_speed_10m,precipitation,weather_code,snowfall
              → weather forecast keyed by stadium coordinates
```

### Recommended Project Structure (Phase 2 additions)

```
backend/app/
├── api/v1/
│   └── team.py              # New: all /team/* routes
├── services/
│   ├── projection_service.py  # New: FantasyCalc + Sleeper merge
│   ├── lineup_optimizer.py    # New: slot assignment algorithm
│   ├── waiver_ranker.py       # New: trend-weighted + composite
│   ├── trade_evaluator.py     # New: FantasyCalc value wrapper
│   └── weather_service.py     # New: Open-Meteo + stadium lookup
└── data/
    └── nfl_stadiums.py        # New: static dict {team_abbr: {lat, lon, indoor}}

frontend/src/
├── pages/
│   └── TeamPage.tsx           # Extend: add cards, drawer, switcher
├── components/
│   ├── LeagueSwitcher.tsx     # New: dropdown in nav/top area
│   ├── LineupCard.tsx         # New: current vs optimal side-by-side
│   ├── WaiverCard.tsx         # New: ranked waiver list with mode toggle
│   ├── PlayerDetailDrawer.tsx # New: Radix Dialog with full player panel
│   ├── WeatherChip.tsx        # New: wind/rain/snow indicator
│   └── TrendChart.tsx         # New: Recharts weekly points trend
└── store/
    └── league.ts              # New: activeLeagueId + lineupOverrides
```

### Pattern 1: FantasyCalc Cache-Aside with arq Pre-Warm

**What:** FantasyCalc data is fetched on first request, cached 24h in Redis. Optional arq background task pre-warms at midnight.
**When to use:** Any endpoint that needs trade values or rankings.

```python
# Source: existing CacheKey/CacheTTL pattern from app/core/cache.py
import json
import httpx
from app.core.cache import CacheKey, CacheTTL

FANTASYCALC_BASE = "https://api.fantasycalc.com"

async def get_fantasycalc_values(redis, is_dynasty: bool = False) -> list[dict]:
    key = f"fantasycalc:values:{'dynasty' if is_dynasty else 'redraft'}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{FANTASYCALC_BASE}/values/current",
            params={"isDynasty": str(is_dynasty).lower(), "numQbs": 1, "numTeams": 12, "ppr": 1},
        )
        r.raise_for_status()
    data = r.json()
    await redis.set(key, json.dumps(data), ex=86400)  # 24h
    return data
```

### Pattern 2: Lineup Optimizer (Greedy Slot Assignment)

**What:** Given a roster of player_ids and the league's `roster_format` (from Roster.snapshot and League.roster_format JSONB), assign players to slots maximizing total FantasyCalc value while respecting position eligibility.
**When to use:** `GET /api/v1/team/lineup`

```python
# Source: [ASSUMED] — standard greedy assignment for positional lineups
# roster_format example from Sleeper: {"positions": ["QB","RB","RB","WR","WR","TE","FLEX","BN","BN"]}
# player eligibility: from /v1/players/nfl player["fantasy_positions"] list

def build_optimal_lineup(
    roster_player_ids: list[str],
    player_lookup: dict,           # player_id -> Sleeper player object
    fc_value_lookup: dict,         # player_id (via sleeperId) -> FantasyCalc entry
    roster_positions: list[str],   # from League.roster_format["positions"]
) -> list[dict]:
    """Greedy descent: fill highest-value non-bench slots first."""
    STARTER_SLOTS = [p for p in roster_positions if p != "BN" and p != "IR"]
    bench_count = roster_positions.count("BN")
    
    # Score each player
    scored = []
    for pid in roster_player_ids:
        player = player_lookup.get(pid, {})
        fc = fc_value_lookup.get(pid)
        injury = player.get("injury_status") or player.get("status", "Active")
        is_out = injury in ("Out", "IR", "Suspended", "PUP", "NA")
        value = (fc["value"] if fc else 0) * (0.1 if is_out else 1.0)
        scored.append({
            "player_id": pid,
            "value": value,
            "eligible_positions": player.get("fantasy_positions", []),
            "injury_status": injury,
        })
    
    scored.sort(key=lambda x: -x["value"])
    # ... slot assignment loop
```

### Pattern 3: Waiver Wire Scoring (Dual Mode)

**What:** Compute both trend-weighted and composite scores for every available player. Return both; frontend toggles display mode.
**When to use:** `GET /api/v1/team/waiver`

```python
# Source: [ASSUMED] — derived from CONTEXT.md DECISION-003

def score_waiver_player(
    player_id: str,
    trending_count: int,        # from Sleeper trending/add
    fc_value: int,              # from FantasyCalc
    recent_pts: float,          # pts_ppr last 2 weeks average
    season_avg_pts: float,
    team_needs: list[str],      # positions the current user's team is weak at
    injury_status: str,
) -> dict:
    # Trend-weighted: recent > historical
    trend_score = (recent_pts * 0.7 + season_avg_pts * 0.3) * (1 + trending_count / 100)
    
    # Composite: equal weight across signals
    positional_need_bonus = 1.2 if player_position in team_needs else 1.0
    injury_penalty = 0.5 if injury_status in ("Questionable", "Doubtful") else 1.0
    composite_score = (
        (fc_value / 10000) * 0.35 +
        trend_score * 0.35 +
        (trending_count / 50) * 0.15 +
        (1 - injury_penalty * 0.5) * 0.15
    ) * positional_need_bonus
    
    return {"trend_score": trend_score, "composite_score": composite_score}
```

### Pattern 4: Open-Meteo Weather Fetch

**What:** Fetch hourly forecast for NFL stadium coordinates; extract wind speed, precipitation, and weather code at game kickoff time.
**When to use:** `GET /api/v1/team/lineup` and player detail panel weather chip.

```python
# Source: [VERIFIED: open-meteo.com/en/docs]
# No API key required. CORS unrestricted.

NFL_STADIUMS = {
    "KC": {"lat": 39.0490, "lon": -94.4839, "indoor": False, "name": "Arrowhead"},
    "BUF": {"lat": 42.7738, "lon": -78.7870, "indoor": False, "name": "Highmark"},
    "LV": {"lat": 36.0909, "lon": -115.1833, "indoor": True, "name": "Allegiant"},
    # ... all 32 teams; ~9 indoor/dome stadiums
}

WEATHER_IMPACT_THRESHOLD = 20  # mph wind for projection downgrade

async def get_game_weather(team_abbr: str, game_date: str) -> dict | None:
    stadium = NFL_STADIUMS.get(team_abbr)
    if not stadium or stadium["indoor"]:
        return None
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": stadium["lat"],
                "longitude": stadium["lon"],
                "hourly": "wind_speed_10m,precipitation,weather_code,snowfall",
                "wind_speed_unit": "mph",
                "forecast_days": 7,
            }
        )
        r.raise_for_status()
    # Parse hourly slot nearest to kickoff time (1pm or 4pm ET Sunday)
    return _extract_kickoff_weather(r.json(), game_date)
```

### Pattern 5: League Switcher Zustand Store

**What:** New `league.ts` store tracks `activeLeagueId` and `lineupOverrides`. React Query queries key on `activeLeagueId` so all data re-fetches on switch.
**When to use:** Phase 2 multi-league navigation.

```typescript
// Source: [ASSUMED] — follows existing auth.ts Zustand persist pattern
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LineupOverride {
  [slot: string]: string  // slot_type -> player_id
}

interface LeagueState {
  activeLeagueId: string | null
  weekOverrides: Record<number, LineupOverride>  // week -> overrides
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
    { name: 'ffhub-league' },
  ),
)
```

### Pattern 6: TrendChart with Recharts

**What:** Line chart showing weekly fantasy points for a player across weeks.
**When to use:** TM-13 per-player trend chart in detail drawer.

```typescript
// Source: [CITED: recharts.org docs]
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

### Anti-Patterns to Avoid

- **Calling FantasyCalc from the browser:** FantasyCalc CORS is `*` today, but that can change without notice. Always proxy through backend and cache. Direct browser calls also expose the caching strategy to users.
- **Hardcoding current NFL season:** Phase 1 established the pattern — always call `GET /v1/state/nfl` and read `season`. Do not hardcode "2026".
- **Loading all 5MB of Sleeper players on every request:** Cache `/v1/players/nfl` for 24h in Redis. Key: `sleeper:players:nfl`. This response is a flat dict keyed by player_id.
- **Treating FantasyCalc `value` as points:** It is a relative trade value (0–10000+ scale), not a projected point total. Display as "trade value" or use normalized rank for projected point estimates.
- **Assuming projections endpoint has data:** Sleeper's `/v1/projections/nfl/{season}/{week}` returns empty objects for all players in the 2026 off-season (confirmed). Fall back to `search_rank` from the players endpoint as the ranking proxy during off-season.
- **Showing weather for indoor stadiums:** 9 of 32 NFL teams play indoors (Allegiant, SoFi, Lucas Oil, Ford Field, US Bank, Mercedes-Benz, State Farm, AT&T, NRG). Build the indoor flag into the stadium lookup table.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-and-drop slot reorder | Custom mousemove + pointer tracking | `@dnd-kit/sortable` | Accessibility (keyboard nav), touch, cross-browser pointer events, screen readers all handled |
| SVG weekly trend chart | `<svg>` + manual path calculations | `recharts` LineChart | Tooltips, responsive container, axis labels — hours of work handled |
| Positional slot constraint solver | Custom backtracking algorithm | Greedy descent (documented above) | Fantasy lineup slots are not complex enough to need LP/ILP; greedy is O(n) and sufficient |
| Weather data fetching + parsing | OpenWeatherMap account + WMO code parsing | Open-Meteo + WMO code table | Free, no key, standard WMO codes map cleanly to rain/snow/wind conditions |
| Player cross-reference between Sleeper and FantasyCalc | Manual fuzzy name matching | `player["sleeperId"]` field on FantasyCalc response | FantasyCalc player objects include `sleeperId` — direct join, no fuzzy matching needed |
| FAAB bid formula | Black-box ML model | Simple percentile-based formula | Off-season/no training data; simple formula is explainable and sufficient for V1 |

**Key insight:** FantasyCalc includes `sleeperId` in every player object, which is the join key between FantasyCalc values and Sleeper player data. This eliminates all fuzzy name-matching complexity.

---

## Common Pitfalls

### Pitfall 1: FantasyCalc Endpoint URL Has Changed

**What goes wrong:** The CONTEXT.md documents `GET /values?sport=nfl&isSuperflex=false` but that URL returns 404. The URL previously documented in articles (`/values/current`) also returns 404 without query params. The working URL requires the query string.
**Why it happens:** FantasyCalc has changed their API paths over time; older documentation is stale.
**How to avoid:** Use `GET /values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1` (confirmed 200 + data on 2026-06-26).
**Warning signs:** 404 response from `api.fantasycalc.com` — check the exact URL with query params.

### Pitfall 2: FantasyCalc Returns Only 200 Players (Redraft) or 460 (Dynasty)

**What goes wrong:** The redraft endpoint returns only the top 200 players. Players outside the top 200 by trade value return no entry.
**Why it happens:** FantasyCalc only exposes valued players, not the full NFL player pool.
**How to avoid:** For waiver wire, use Sleeper's full `/v1/players/nfl` as the player source; use FantasyCalc values for ranked players, and treat missing entries as "low value" (value = 0).
**Warning signs:** Waiver wire shows only 30 players — means code is filtering to only FantasyCalc-covered players.

### Pitfall 3: Sleeper injury_status Is Null During Off-Season

**What goes wrong:** During the off-season (current state: `season_type: "off"`), all players have `injury_status: null` or `""`. Injury display logic that checks for null will mark all players as "Active" which is correct but the data is stale.
**Why it happens:** Sleeper injury data is in-season only.
**How to avoid:** Gate injury chip display on `season_type !== "off"` from the cached NFL state. During off-season, do not show injury badges.
**Warning signs:** All players show "Active" status during testing — confirm it's because off-season, not a bug.

### Pitfall 4: Sleeper `roster.snapshot.starters` Contains Empty String IDs

**What goes wrong:** Sleeper's `starters` array includes `"0"` or `""` for unfilled slots. Treating these as player_ids causes 404 lookups.
**Why it happens:** Sleeper pads the starters array to match the exact count of starter slots, using `"0"` for empty slots.
**How to avoid:** Filter starters with `[s for s in starters if s and s != "0"]` before lookups.
**Warning signs:** KeyError or null player objects in lineup output.

### Pitfall 5: Open-Meteo Returns Wind Speed in km/h by Default

**What goes wrong:** TM-09 threshold is 20 mph. Without `wind_speed_unit=mph`, Open-Meteo returns km/h. 20 km/h (~12.4 mph) is very different from 20 mph.
**Why it happens:** Open-Meteo default unit is metric.
**How to avoid:** Always include `wind_speed_unit=mph` in Open-Meteo requests. Or convert: mph = km/h × 0.621371.
**Warning signs:** Weather chip shows for mild conditions (e.g., "18 mph wind" but it was actually 18 km/h ≈ 11 mph).

### Pitfall 6: React Query Cache Not Invalidated on League Switch

**What goes wrong:** User switches leagues; lineup still shows previous league's data because React Query served from cache.
**Why it happens:** Query keys don't include `activeLeagueId`.
**How to avoid:** Include `activeLeagueId` in every query key: `queryKey: ['team-lineup', activeLeagueId]`. React Query will re-fetch when the key changes.
**Warning signs:** League name in header updates but lineup/waiver data doesn't.

### Pitfall 7: No Waiver Data in Off-Season

**What goes wrong:** Sleeper's trending endpoint (`/players/nfl/trending/add`) returns very low counts during off-season, making trend-weighted scores meaningless.
**Why it happens:** Trending add data is volume-driven; nobody is adding players in June.
**How to avoid:** During off-season (`season_type: "off"`), fall back to composite-only mode and disable the trend-weighted toggle with a "In-season only" tooltip.
**Warning signs:** All waiver scores cluster near 0.

---

## Code Examples

### FantasyCalc Player Lookup by Sleeper ID (Verified Response Shape)

```python
# Source: [VERIFIED: live API call 2026-06-26]
# Actual response fields confirmed from https://api.fantasycalc.com/values/current?...
# 
# Top-level entry:
# {
#   "player": {
#     "id": 9833, "name": "Bijan Robinson", "sleeperId": "9509",
#     "position": "RB", "maybeTeam": "ATL", "maybeAge": 24.4
#   },
#   "value": 10429,          # trade value (0-12000+ scale)
#   "overallRank": 1,
#   "positionRank": 1,
#   "trend30Day": -77,       # value change over 30 days (negative = decreasing)
#   "maybeTier": 1,          # tier 1 = elite
#   "maybeAdp": null,        # sometimes populated
#   "maybeRosterPercent": 0.9825,  # % of leagues rostered
#   "redraftValue": 10429,
#   "combinedValue": 20858   # redraft + dynasty combined
# }

def build_sleeper_id_index(fc_values: list[dict]) -> dict[str, dict]:
    """Build index from Sleeper player_id -> FantasyCalc entry."""
    return {
        entry["player"]["sleeperId"]: entry
        for entry in fc_values
        if entry["player"].get("sleeperId")
    }
```

### Sleeper Stats Endpoint (Verified Response Shape)

```python
# Source: [VERIFIED: live API call 2026-06-26]
# GET https://api.sleeper.app/v1/stats/nfl/regular/2024/1
# Returns: dict keyed by player_id (string)
# Each player value (example QB):
# {
#   "pass_yd": 167, "pass_td": 1, "pass_att": 21, "pass_cmp": 13,
#   "rush_yd": -1, "gp": 1, "pts_ppr": 9.58, "pts_std": 9.58,
#   "pos_rank_ppr": 26, "off_snp": 38, "tm_off_snp": 51
# }
# Key fields for Phase 2:
#   pts_ppr / pts_half_ppr / pts_std — actual scored points
#   pos_rank_ppr — position rank that week
#   off_snp / tm_off_snp — snap count (usage proxy)

async def get_player_weekly_stats(season: str, week: int, redis) -> dict[str, dict]:
    key = f"sleeper:stats:{season}:{week}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}")
        r.raise_for_status()
    data = r.json()
    await redis.set(key, json.dumps(data), ex=3600)  # 1h TTL
    return data
```

### Sleeper Injury Status Values (Verified)

```python
# Source: [VERIFIED: support.sleeper.com/en/articles/3570017-player-status-and-gameday-designations]
INJURY_SEVERITY = {
    None: 0,         # no designation
    "": 0,
    "Active": 0,
    "Questionable": 1,
    "Doubtful": 2,
    "Out": 3,
    "Suspended": 3,
    "IR": 4,
    "PUP": 4,
    "NA": 4,
    "DNR": 4,        # Did Not Return
}

PLAYS_STATUS = {"Active", None, "", "Questionable"}  # may play
UNLIKELY_STATUS = {"Doubtful"}                        # probably out
WONT_PLAY_STATUS = {"Out", "Suspended", "IR", "PUP", "NA", "DNR"}
```

### dnd-kit Sortable Lineup (Verified API)

```typescript
// Source: [CITED: dndkit.com/react/quickstart]
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function SortablePlayerCard({ slot }: { slot: RosterSlot }) {
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

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `react-beautiful-dnd` | `@dnd-kit/core` | Atlassian archived react-beautiful-dnd 2023 | Must use dnd-kit or hello-pangea/dnd fork; react-beautiful-dnd has React 18 issues |
| `react-chartjs-2` | `recharts` | Ongoing preference shift | Recharts is React-native (JSX composable); no canvas vs SVG trade-off for small datasets |
| FantasyCalc `/values?sport=nfl` | FantasyCalc `/values/current?isDynasty=false&numQbs=1&numTeams=12&ppr=1` | URL format changed (exact date unknown) | CONTEXT.md documents old URL format — must use `/values/current` with query params |

**Deprecated/outdated:**
- `react-beautiful-dnd`: Archived. Community fork `@hello-pangea/dnd` exists but dnd-kit is the better long-term choice.
- Sleeper projections endpoint: Returns empty for off-season. Not reliable as a primary data source for V1 (off-season development).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Sleeper projections endpoint will populate with real data during the 2026 NFL season (currently empty off-season) | Standard Stack / Architecture | Optimizer will have no projection data; must rely on FantasyCalc values only for ranking — already the design, so low impact |
| A2 | Open-Meteo free tier has no rate limits that would affect production usage | Standard Stack | May need to add API key or switch to WeatherAPI.com; weather caching per game day mitigates this |
| A3 | FantasyCalc `/values/current` endpoint URL and parameter format is stable | Standard Stack | If URL changes again, all trade value lookups break; 24h Redis TTL provides a buffer |
| A4 | Greedy descent lineup optimizer is sufficient (no ILP needed) | Architecture Patterns | For unusual roster formats (e.g., 3-FLEX leagues), greedy may produce suboptimal lineups — acceptable for V1 |
| A5 | TM-11 (positive game script: RB on team favored 10+) requires external odds data | Phase Requirements | Sleeper matchup data does not include point spreads; need to either add an odds API or drop this signal |
| A6 | TM-14 (player news feed) will use a third-party news source not yet selected | Phase Requirements | If no free news source is found, TM-14 must be scoped down or deferred |
| A7 | FantasyCalc does not rate-limit server-side requests caching to 24h TTL | Standard Stack | If rate limited, need to add User-Agent header or contact FantasyCalc; no documented rate limits found |
| A8 | NFL stadium indoor/outdoor static table can be hardcoded for Phase 2 | Architecture Patterns | If a team relocates or builds a new stadium mid-season, table is stale — negligible risk for V1 |

---

## Open Questions (RESOLVED 2026-06-26)

All three open questions from initial research have been resolved. Plans updated accordingly.

1. **TM-14: Player news feed data source — RESOLVED: DEFERRED**
   - Resolution: No free structured news source with timestamp + impact tag was identified for Phase 2.
   - Phase 2 delivers `news: []` (empty array) on each lineup slot. PlayerDetailDrawer hides the news
     section entirely when the array is empty (per UI-SPEC: hide, not empty-state).
   - TM-14 will be addressed in Phase 2b or Phase 3 when a data source is selected.
   - Impact: Plans 02-11 and 02-12 updated. Backend slot response includes `news: []`.

2. **TM-11: Point spread data — RESOLVED: SLEEPER MATCHUP PROXY**
   - Resolution: Use Sleeper matchup history as a spread proxy via `GET /v1/league/{id}/matchups/{week}`
     (already fetched for lineup context). Compute each team's season-average pts_for over last 4 weeks.
   - Rule: if player's team pts_for_avg >= 25.0 AND opponent pts_against_avg >= 25.0, set
     `positive_game_script = True` for RB position players only.
   - This is a win-likelihood proxy, not a Vegas spread. UI copy: 'Based on matchup history.'
   - Implemented in `LineupOptimizer._compute_game_script()`. Team stats passed as
     `team_matchup_stats: dict[str, float]`, computed once per `/team/lineup` request.
   - Impact: Plan 02-12 Task 1 updated to implement `_compute_game_script()` instead of hardcoding False.

3. **FantasyCalc rankings endpoint — RESOLVED: USE overallRank FROM /values/current**
   - Resolution: Use `overallRank` and `positionRank` fields from the `/values/current` response.
     No separate rankings endpoint exists; all tested variants return 404.
   - `overallRank` is populated on every player entry in the confirmed live response.
   - Impact: CONTEXT.md DECISION-001 updated to remove the `/rankings` entry.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build | ✓ | (npm confirmed working) | — |
| PostgreSQL | All DB reads | ✓ | (from Phase 1 docker-compose) | — |
| Redis | Cache layer | ✓ | (from Phase 1 docker-compose) | — |
| FantasyCalc API | TM-01, TM-06, TM-08, TM-13, TM-14 | ✓ | `/values/current` confirmed 200 2026-06-26 | — |
| Sleeper API (players, stats, trending) | TM-01–07 | ✓ | Confirmed from Phase 1 + new endpoints tested | — |
| Open-Meteo | TM-09 | ✓ | Confirmed 200, no API key | — |
| Player news source | TM-14 | ✗ | — | Defer TM-14 or use RotoWire RSS (free, unstructured) |
| Odds/spread API | TM-11 | ✗ | — | The Odds API free tier (500 req/mo); or drop game script signal |

**Missing dependencies with no fallback:**
- Player news API (structured, with timestamp and impact tag): TM-14 is blocked pending source selection.

**Missing dependencies with fallback:**
- Odds/spread data: The Odds API free tier or omit TM-11's spread signal.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 + pytest-asyncio 0.23.0 [VERIFIED: pyproject.toml] |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_team.py -x` |
| Full suite command | `pytest tests/ --cov=app` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TM-01 | LineupOptimizer assigns starters correctly for standard roster | unit | `pytest tests/test_lineup_optimizer.py -x` | ❌ Wave 0 |
| TM-01 | LineupOptimizer respects injury OUT status | unit | `pytest tests/test_lineup_optimizer.py::test_injured_player_excluded -x` | ❌ Wave 0 |
| TM-04 | OUT player triggers replacement suggestion | unit | `pytest tests/test_lineup_optimizer.py::test_out_replacement -x` | ❌ Wave 0 |
| TM-05 | WaiverRanker returns 30+ targets | unit | `pytest tests/test_waiver_ranker.py::test_minimum_30_targets -x` | ❌ Wave 0 |
| TM-05 | Trend-weighted score > composite for breakout player | unit | `pytest tests/test_waiver_ranker.py::test_trend_vs_composite -x` | ❌ Wave 0 |
| TM-07 | FAAB league returns FAAB UI fields; rolling priority returns priority field | unit | `pytest tests/test_team_routes.py::test_waiver_type_detection -x` | ❌ Wave 0 |
| TM-09 | Weather chip not shown for indoor stadiums | unit | `pytest tests/test_weather_service.py::test_indoor_no_chip -x` | ❌ Wave 0 |
| TM-09 | Wind ≥20 mph triggers chip | unit | `pytest tests/test_weather_service.py::test_wind_threshold -x` | ❌ Wave 0 |
| Route: /team/my | Returns 200 with team data for authenticated user | integration | `pytest tests/test_team_routes.py::test_get_my_team -x` | ❌ Wave 0 |
| Route: /team/lineup | Returns optimal lineup with confidence scores | integration | `pytest tests/test_team_routes.py::test_get_lineup -x` | ❌ Wave 0 |
| Route: /team/waiver | Returns ranked waiver list with both scores | integration | `pytest tests/test_team_routes.py::test_get_waiver -x` | ❌ Wave 0 |
| LC-09 carryover | /team/* routes return 404 for wrong user's league | integration | `pytest tests/test_team_routes.py::test_isolation -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_team.py tests/test_team_routes.py -x`
- **Per wave merge:** `pytest tests/ --cov=app`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_lineup_optimizer.py` — covers TM-01, TM-04
- [ ] `tests/test_waiver_ranker.py` — covers TM-05, TM-06, TM-07
- [ ] `tests/test_weather_service.py` — covers TM-09
- [ ] `tests/test_team_routes.py` — covers route-level integration for all five /team/* endpoints
- [ ] `tests/fixtures/fc_values_sample.json` — sample FantasyCalc response for deterministic test data (20 players)
- [ ] `tests/fixtures/sleeper_players_sample.json` — sample Sleeper player dict (10 players matching fc_values_sample)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | JWT via existing `get_current_user` dep — all /team/* routes must use it |
| V3 Session Management | no | Handled in Phase 1 |
| V4 Access Control | yes | Row-level isolation: /team/* must resolve through `get_league_for_user` so user A can't query user B's team |
| V5 Input Validation | yes | Pydantic models on all request bodies; `league_id` as UUID type (auto-validates format) |
| V6 Cryptography | no | No new secrets in Phase 2; FantasyCalc and Open-Meteo are public APIs |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Accessing another user's team data via league_id | Spoofing / Info Disclosure | `get_league_for_user` dep joins through `league_members` WHERE user_id = current_user.id; returns 404 not 403 |
| Overloading Open-Meteo or FantasyCalc via user-triggered requests | Denial of Service | Cache FantasyCalc 24h, Open-Meteo per game-day; user cannot bypass cache via API |
| Client-supplied override data for lineup (TM-15) | Tampering | Overrides are stored client-side only (Zustand localStorage); server never accepts lineup slot as authoritative — server always computes optimal independently |

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: live API call 2026-06-26] FantasyCalc `/values/current` — confirmed response shape, 200 players (redraft), 460 (dynasty), CORS `access-control-allow-origin: *`, player fields including `sleeperId` join key
- [VERIFIED: live API call 2026-06-26] Sleeper `/v1/stats/nfl/regular/2024/1` — confirmed stats fields (pts_ppr, pass_yd, rush_yd, off_snp, pos_rank_ppr)
- [VERIFIED: live API call 2026-06-26] Sleeper `/v1/state/nfl` — current state structure confirmed (season, week, season_type)
- [VERIFIED: live API call 2026-06-26] Open-Meteo `/v1/forecast` — confirmed wind_speed_10m, weather_code, precipitation, snowfall fields; no API key required
- [VERIFIED: npm registry 2026-06-26] `@dnd-kit/core` 6.3.1, `@dnd-kit/sortable` 10.0.0, `recharts` 3.9.0
- [VERIFIED: codebase] `package.json`, `pyproject.toml`, `app/core/cache.py`, `app/services/sleeper_client.py` — existing Phase 1 patterns

### Secondary (MEDIUM confidence)

- [CITED: docs.sleeper.com] Sleeper API endpoint list including `/v1/players/nfl/trending/add`, `/v1/league/{id}/matchups/{week}`, `/v1/league/{id}/transactions/{round}`
- [CITED: support.sleeper.com/en/articles/3570017] Sleeper injury_status value enumeration (Active, Questionable, Doubtful, Out, Suspended, IR, PUP, NA, DNR)
- [CITED: open-meteo.com/en/docs] Open-Meteo variable names, forecast endpoint, no rate-limit for non-commercial use
- [CITED: fantasydatapros.com/fantasyfootball/blog/fantasycalc/1] FantasyCalc full player object field structure (all 19 top-level fields confirmed against live response)
- [CITED: dndkit.com] dnd-kit `useSortable`, `SortableContext`, `arrayMove` API

### Tertiary (LOW confidence)

- [ASSUMED] Sleeper projections endpoint will populate with data when 2026 season starts
- [ASSUMED] FantasyCalc does not enforce rate limits on server-to-server requests
- [WebSearch verified partially] react-beautiful-dnd is archived; dnd-kit and hello-pangea/dnd are the current alternatives

---

## Metadata

**Confidence breakdown:**
- FantasyCalc API: HIGH — live API call confirmed URL, response shape, CORS headers
- Sleeper API (players, stats, matchups): HIGH — live API confirmed; docs reviewed
- Open-Meteo: HIGH — live API confirmed
- dnd-kit + recharts: HIGH — npm versions confirmed; APIs cited from official docs
- Lineup optimizer algorithm: LOW-MEDIUM — greedy approach is ASSUMED; no authoritative source for "correct" fantasy optimizer design
- Waiver scoring formula weights: LOW — weights are ASSUMED; will need tuning
- TM-11 (game script) implementation path: LOW — odds data source not yet selected
- TM-14 (news feed) implementation path: LOW — data source not yet identified

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 for stable items (APIs, npm versions); FantasyCalc URL should be re-verified if more than 30 days old
