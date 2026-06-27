"""Redis key builders and TTL constants for Phase 1.

All keys follow patterns defined in ARCHITECTURE.md Section 5.
TTLs are in seconds.
"""


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


class CacheTTL:
    SLEEPER_USER: int = 300       # 5 min
    SLEEPER_LEAGUES: int = 600    # 10 min
    LEAGUE_SETTINGS: int = 21600  # 6 hours
    LEAGUE_MEMBERS: int = 21600   # 6 hours
    LEAGUE_ROSTERS: int = 1800    # 30 min
    NFL_STATE: int = 3600         # 1 hour
    FANTASYCALC: int = 86400      # 24 hours — FantasyCalc values change infrequently
    SLEEPER_PLAYERS: int = 86400  # 24 hours — full player pool, 5MB, expensive to refetch
    SLEEPER_STATS: int = 3600     # 1 hour — per-week stats (finalized after game)
    SLEEPER_TRENDING: int = 3600  # 1 hour — add/drop counts during season
    OPEN_METEO: int = 21600       # 6 hours — once per game day is sufficient


async def get_or_set(redis, key: str, fetch_fn, ttl: int) -> str:
    """Cache-aside helper: return cached value or call fetch_fn, cache result, return it.

    fetch_fn must be an async callable returning a JSON-serializable string.
    Returns the raw string (caller is responsible for json.loads if needed).
    """
    cached = await redis.get(key)
    if cached is not None:
        return cached
    value = await fetch_fn()
    await redis.set(key, value, ex=ttl)
    return value
