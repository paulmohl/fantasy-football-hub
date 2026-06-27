"""Team Manager routes — /api/v1/team/*.

All routes except /my use get_league_for_user which enforces row-level isolation:
user A cannot query user B's league data (LC-09 carryover).

Route list:
  GET  /my              -> active league team info (user-scoped)
  GET  /lineup          -> optimal lineup with confidence scores (TM-01, TM-02, TM-04)
  GET  /waiver          -> ranked waiver wire, dual-mode (TM-05, TM-06, TM-07)
  GET  /standings       -> league matchup standings (TM-07)
  GET  /trade           -> head-to-head player comparison (TM-08)
  POST /lineup/apply    -> TM-16 stub: 501 Not Implemented (Phase 3+)
"""
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey, CacheTTL
from app.core.database import get_db
from app.core.deps import get_current_user, get_league_for_user
from app.core.logging import logger
from app.core.redis import get_redis
from app.models.league import League, LeagueMember, Roster, Team
from app.models.user import User
from app.services.lineup_optimizer import LineupOptimizer, build_optimal_lineup
from app.services.projection_service import ProjectionService, get_projection_service
from app.services.sleeper_client import SleeperClient, get_sleeper_client
from app.services.trade_evaluator import compare_players
from app.services.waiver_ranker import (
    detect_waiver_type,
    rank_waiver_wire,
    recommend_faab_bid,
    suggest_drop_candidates,
)
from app.services.weather_service import WeatherService, get_weather_service

router = APIRouter(prefix="/team", tags=["team"])


async def _get_nfl_state(redis: Redis, sleeper: SleeperClient) -> dict:
    """Fetch current NFL state; never hardcode season (RESEARCH.md anti-pattern)."""
    cached = await redis.get(CacheKey.nfl_state())
    if cached:
        return json.loads(cached)
    state = await sleeper.get_nfl_state()
    await redis.set(CacheKey.nfl_state(), json.dumps(state), ex=CacheTTL.NFL_STATE)
    return state


async def _get_user_team_and_roster(
    league: League,
    current_user: User,
    db: AsyncSession,
    week: int = 1,
) -> tuple["Team | None", "Roster | None"]:
    """Fetch the current user's Team and their Roster snapshot for a league.

    Teams are matched by owner_user_id. Rosters are matched by team_id + week.
    Returns (None, None) if user has no team in this league yet.
    """
    team_result = await db.execute(
        select(Team)
        .where(Team.league_id == league.id)
        .where(Team.owner_user_id == current_user.id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        return None, None

    roster_result = await db.execute(
        select(Roster)
        .where(Roster.team_id == team.id)
        .where(Roster.week == week)
        .order_by(Roster.week.desc())
    )
    roster = roster_result.scalar_one_or_none()
    return team, roster


async def _compute_team_matchup_stats(
    league_id: str,
    current_week: int,
    sleeper: SleeperClient,
    redis: Redis,
) -> dict[int, dict[str, float]]:
    """Compute pts_for_avg and pts_against_avg for each team over last 4 weeks.

    Returns dict keyed by roster_id:
        {roster_id: {"pts_for_avg": float, "pts_against_avg": float}}
    """
    weeks_back = min(4, current_week - 1)
    if weeks_back < 1:
        return {}

    roster_points: dict[int, list[float]] = {}
    matchup_id_to_roster: dict[int, dict[int, list[tuple[int, float]]]] = {}

    for w in range(max(1, current_week - weeks_back), current_week):
        cache_key = f"sleeper:matchups:{league_id}:{w}"
        cached = await redis.get(cache_key)
        if cached:
            week_data = json.loads(cached)
        else:
            week_data = await sleeper.get_league_matchups(league_id, w)
            await redis.set(cache_key, json.dumps(week_data), ex=3600)

        for entry in week_data:
            rid = entry.get("roster_id")
            pts = float(entry.get("points") or 0)
            mid = entry.get("matchup_id")
            if rid is None:
                continue
            roster_points.setdefault(rid, []).append(pts)
            if mid:
                matchup_id_to_roster.setdefault(w, {}).setdefault(mid, []).append((rid, pts))

    result: dict[int, dict[str, float]] = {}
    for rid, pts_list in roster_points.items():
        result[rid] = {
            "pts_for_avg": sum(pts_list) / len(pts_list),
            "pts_against_avg": 0.0,
        }

    opponent_pts: dict[int, list[float]] = {}
    for w_data in matchup_id_to_roster.values():
        for mid, pairs in w_data.items():
            if len(pairs) == 2:
                r1, p1 = pairs[0]
                r2, p2 = pairs[1]
                opponent_pts.setdefault(r1, []).append(p2)
                opponent_pts.setdefault(r2, []).append(p1)

    for rid, opp_list in opponent_pts.items():
        if rid in result and opp_list:
            result[rid]["pts_against_avg"] = sum(opp_list) / len(opp_list)

    return result


@router.get("/my")
async def get_my_team(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's connected leagues and their active team info.

    Used by frontend to initialize the league switcher and TeamPage.
    """
    result = await db.execute(
        select(League, LeagueMember)
        .join(LeagueMember, LeagueMember.league_id == League.id)
        .where(LeagueMember.user_id == current_user.id)
        .order_by(LeagueMember.connected_at.desc())
    )
    rows = result.all()

    leagues = []
    for league, member in rows:
        # Try to find the user's team in this league
        team_result = await db.execute(
            select(Team)
            .where(Team.league_id == league.id)
            .where(Team.owner_user_id == current_user.id)
        )
        team = team_result.scalar_one_or_none()
        leagues.append({
            "league_id": str(league.id),
            "name": league.name,
            "season": league.season,
            "platform": league.host_platform,
            "host_team_id": team.host_team_id if team else None,
            "team_name": team.name if team else None,
        })

    return {"leagues": leagues, "user_id": str(current_user.id)}


@router.get("/lineup")
async def get_lineup(
    league: League = Depends(get_league_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    projection: ProjectionService = Depends(get_projection_service),
    sleeper: SleeperClient = Depends(get_sleeper_client),
    weather: WeatherService = Depends(get_weather_service),
):
    """Return optimal lineup vs current lineup with confidence scores and swap badges (TM-01, TM-02, TM-04)."""
    nfl_state = await _get_nfl_state(redis, sleeper)
    season = nfl_state["season"]
    week = int(nfl_state.get("week", 1))

    team, roster = await _get_user_team_and_roster(league, current_user, db, week)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found in this league")
    if not roster or not roster.snapshot:
        raise HTTPException(status_code=404, detail="Roster snapshot not found — refresh your league")

    # Fetch data layer
    fc_values = await projection.get_fantasycalc_values(is_dynasty=False)
    players = await projection.get_sleeper_players()
    fc_index = projection.build_sleeper_id_index(fc_values)

    roster_ids: list[str] = roster.snapshot.get("players", [])
    current_starters: list[str] = [
        pid for pid in roster.snapshot.get("starters", []) if pid and pid != "0"
    ]
    positions: list[str] = (league.roster_format or {}).get("positions", [])

    # build_optimal_lineup returns a list of slot dicts (not a tuple)
    optimal_slots = build_optimal_lineup(
        roster_player_ids=roster_ids,
        player_lookup=players,
        fc_index=fc_index,
        roster_positions=positions,
        current_starters=current_starters,
    )

    # Compute team matchup stats for TM-11 game script and TM-03 matchup fields
    team_matchup_stats = await _compute_team_matchup_stats(
        league_id=league.host_league_id,
        current_week=week,
        sleeper=sleeper,
        redis=redis,
    )

    # Fetch trending adds for TM-03 recent_usage_trend
    season_type = nfl_state.get("season_type", "off")
    trending_adds: dict[str, int] = {}
    if season_type != "off":
        trending_adds = await projection.get_sleeper_trending()

    # Compute matchup grade rank map (rank by pts_against_avg descending = allows most pts = easiest)
    all_pts_against = sorted(
        [(rid, s.get("pts_against_avg", 0)) for rid, s in team_matchup_stats.items()],
        key=lambda x: -x[1],
    )
    rank_map: dict[int, int] = {rid: i + 1 for i, (rid, _) in enumerate(all_pts_against)}
    total_teams = len(all_pts_against) or 1

    def _grade_from_rank(rank: int, total: int) -> str:
        pct = rank / total
        if pct <= 0.25:
            return "F"
        elif pct <= 0.50:
            return "D"
        elif pct <= 0.75:
            return "C"
        elif pct <= 0.90:
            return "B"
        else:
            return "A"

    optimizer = LineupOptimizer()

    # Look up the user's roster_id from matchup data (needed for game script)
    # The team's host_team_id maps to Sleeper roster_id
    user_roster_id: int | None = None
    if team.host_team_id:
        try:
            user_roster_id = int(team.host_team_id)
        except (ValueError, TypeError):
            user_roster_id = None

    for slot in optimal_slots:
        # TM-11: positive_game_script flag (RB only)
        slot["positive_game_script"] = False
        if slot.get("position") == "RB" and not slot.get("is_out") and user_roster_id is not None:
            slot["positive_game_script"] = optimizer._compute_game_script(
                user_roster_id, team_matchup_stats, "RB"
            )

        # TM-03: matchup_grade (grade how many points opponent allows)
        # We don't have per-slot opponent roster_id in this data model, so use user's own grade
        # as a proxy for overall matchup difficulty this week
        if user_roster_id and user_roster_id in rank_map:
            opp_rank = rank_map.get(user_roster_id)
            slot["matchup_grade"] = _grade_from_rank(opp_rank, total_teams) if opp_rank else None
        else:
            slot["matchup_grade"] = None

        # TM-03: opponent_rank_vs_position (rank 1 = allows most to this position)
        slot["opponent_rank_vs_position"] = rank_map.get(user_roster_id) if user_roster_id else None

        # TM-03: recent_usage_trend from Sleeper trending adds
        player_id = slot.get("player_id")
        current_adds = trending_adds.get(player_id, 0) if player_id else 0
        if current_adds > 0:
            slot["recent_usage_trend"] = "stable"
        else:
            slot["recent_usage_trend"] = None

        # TM-14: news deferred (CONTEXT.md — data source TBD)
        slot["news"] = []

    # Derive summary metadata from the slots
    total_projected = sum(
        slot.get("projected_points", 0)
        for slot in optimal_slots
        if slot.get("slot") not in ("BN", "IR")
    )
    no_strong_call = all(
        slot.get("confidence", 0) < 60
        for slot in optimal_slots
        if slot.get("slot") not in ("BN", "IR")
    )

    # Attach weather data to each player slot (best-effort; skip if no matchup cache)
    matchups_key = f"sleeper:matchups:{league.host_league_id}:{week}"
    cached_matchups = await redis.get(matchups_key)
    matchup_weather: dict[str, dict | None] = {}
    if cached_matchups:
        for slot in optimal_slots:
            pid = slot.get("player_id")
            if pid:
                player_data = players.get(pid, {})
                team_abbr = player_data.get("team")
                if team_abbr and team_abbr not in matchup_weather:
                    w = await weather.get_game_weather(team_abbr, nfl_state.get("display_week", ""))
                    matchup_weather[team_abbr] = w
                slot["weather"] = matchup_weather.get(team_abbr) if team_abbr else None

    logger.info("team.lineup.built", league_id=str(league.id), slots=len(optimal_slots))
    return {
        "league_id": str(league.id),
        "season": season,
        "week": week,
        "optimal_lineup": optimal_slots,
        "current_starters": current_starters,
        "total_projected_points": round(total_projected, 1),
        "no_strong_call": no_strong_call,
        "season_type": season_type,
    }


@router.get("/waiver")
async def get_waiver(
    league: League = Depends(get_league_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    projection: ProjectionService = Depends(get_projection_service),
    sleeper: SleeperClient = Depends(get_sleeper_client),
    mode: Literal["trend", "composite"] = Query(default="composite"),
    player_a: str | None = Query(default=None),
):
    """Return ranked waiver wire targets with dual-mode scores (TM-05, TM-06, TM-07).

    Optional: pass player_a to get add-player drop suggestions for that player.
    """
    nfl_state = await _get_nfl_state(redis, sleeper)
    season = nfl_state["season"]
    week = int(nfl_state.get("week", 1))
    season_type = nfl_state.get("season_type", "off")

    team, roster = await _get_user_team_and_roster(league, current_user, db, week)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found in this league")
    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    fc_values = await projection.get_fantasycalc_values(is_dynasty=False)
    players = await projection.get_sleeper_players()
    fc_index = projection.build_sleeper_id_index(fc_values)

    # Trending counts (empty dict during off-season — see Pitfall 7)
    trending_counts: dict[str, int] = {}
    if season_type != "off":
        trending_counts = await projection.get_sleeper_trending()

    # Stats for recent performance (last week if available)
    recent_pts: dict[str, float] = {}
    season_avg_pts: dict[str, float] = {}
    if season_type != "off" and week > 1:
        week_stats = await projection.get_player_weekly_stats(season, week - 1)
        for pid, stats in week_stats.items():
            recent_pts[pid] = float(stats.get("pts_ppr", 0) or 0)
            season_avg_pts[pid] = float(stats.get("pts_ppr", 0) or 0)

    # Determine rostered player_ids across all teams in the league
    teams_result = await db.execute(
        select(Team).where(Team.league_id == league.id)
    )
    all_teams = teams_result.scalars().all()
    rostered_ids: set[str] = set()
    for t in all_teams:
        roster_result = await db.execute(
            select(Roster)
            .where(Roster.team_id == t.id)
            .where(Roster.week == week)
        )
        r = roster_result.scalar_one_or_none()
        if r and r.snapshot:
            rostered_ids.update(r.snapshot.get("players", []))

    # Determine team positional needs (positions without strong starters)
    snapshot = roster.snapshot or {}
    my_starters = [pid for pid in snapshot.get("starters", []) if pid and pid != "0"]
    team_needs: list[str] = []
    for pos in ["RB", "WR", "TE"]:
        pos_starters = [
            pid for pid in my_starters
            if pos in players.get(pid, {}).get("fantasy_positions", [])
        ]
        if len(pos_starters) < 2:
            team_needs.append(pos)

    ranked = rank_waiver_wire(
        available_player_ids=list(players.keys()),
        player_lookup=players,
        fc_index=fc_index,
        trending_counts=trending_counts,
        recent_pts=recent_pts,
        season_avg_pts=season_avg_pts,
        team_needs=team_needs,
        rostered_ids=rostered_ids,
    )

    # Detect waiver type from scoring_rules (Sleeper stores settings in scoring_rules JSONB)
    waiver_type = detect_waiver_type(league.scoring_rules or {})

    # Optional: drop suggestions for adding player_a
    drop_suggestions = []
    bid = None
    if player_a:
        in_progress: set[str] = set()  # Phase 2: no live game tracking; empty for now
        my_roster_ids = [pid for pid in snapshot.get("players", []) if pid and pid != "0"]
        drop_suggestions = suggest_drop_candidates(
            rostered_ids=my_roster_ids,
            fc_index=fc_index,
            in_progress_ids=in_progress,
            locked_ids=set(),
            player_lookup=players,
        )
        # Add FAAB suggestion if FAAB league
        if waiver_type == "faab" and player_a in fc_index:
            fc_entry = fc_index[player_a]
            # Phase 2: no actual FAAB spend tracking; use full budget as remaining
            faab_budget = int((league.scoring_rules or {}).get("settings", {}).get("waiver_budget", 100))
            bid = recommend_faab_bid(
                player_id=player_a,
                fc_value=fc_entry.get("value", 0),
                remaining_budget=faab_budget,
                positional_scarcity=1.0,
                trend30_day=fc_entry.get("trend30Day", 0),
            )

    logger.info("team.waiver.ranked", league_id=str(league.id), count=len(ranked), mode=mode)
    return {
        "league_id": str(league.id),
        "waiver_type": waiver_type,
        "mode": mode,
        "season_type": season_type,
        "players": ranked[:60],  # cap at 60; frontend paginates
        "drop_suggestions": drop_suggestions,
        "faab_bid": bid,
    }


@router.get("/standings")
async def get_standings(
    league: League = Depends(get_league_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    sleeper: SleeperClient = Depends(get_sleeper_client),
):
    """Return league standings (team records and points)."""
    nfl_state = await _get_nfl_state(redis, sleeper)
    week = int(nfl_state.get("week", 1))

    # Fetch all teams in the league with their owners
    teams_result = await db.execute(
        select(Team, LeagueMember)
        .join(LeagueMember, LeagueMember.league_id == Team.league_id)
        .where(Team.league_id == league.id)
        .where(LeagueMember.user_id == Team.owner_user_id)
    )
    rows = teams_result.all()

    standings = []
    for team, member in rows:
        # Get the latest roster snapshot for this team
        roster_result = await db.execute(
            select(Roster)
            .where(Roster.team_id == team.id)
            .where(Roster.week == week)
        )
        roster = roster_result.scalar_one_or_none()
        snapshot = (roster.snapshot if roster else None) or {}

        standings.append({
            "host_team_id": team.host_team_id,
            "team_name": team.name,
            "user_id": str(team.owner_user_id) if team.owner_user_id else None,
            "is_current_user": team.owner_user_id == current_user.id,
            "wins": snapshot.get("settings", {}).get("wins", 0),
            "losses": snapshot.get("settings", {}).get("losses", 0),
            "pts_for": round(float(snapshot.get("settings", {}).get("fpts", 0)), 2),
            "waiver_position": snapshot.get("settings", {}).get("waiver_position"),
        })

    standings.sort(key=lambda x: (-x["wins"], -x["pts_for"]))
    return {
        "league_id": str(league.id),
        "week": week,
        "standings": standings,
    }


@router.get("/trade")
async def get_trade_comparison(
    league: League = Depends(get_league_for_user),
    projection: ProjectionService = Depends(get_projection_service),
    player_a: str = Query(..., description="Sleeper player_id of first player"),
    player_b: str = Query(..., description="Sleeper player_id of second player"),
):
    """Head-to-head player comparison using FantasyCalc trade values (TM-08)."""
    fc_values = await projection.get_fantasycalc_values(is_dynasty=False)
    players = await projection.get_sleeper_players()
    fc_index = projection.build_sleeper_id_index(fc_values)

    if player_a not in players or player_b not in players:
        raise HTTPException(status_code=404, detail="One or both player IDs not found")

    result = compare_players(
        player_id_a=player_a,
        player_id_b=player_b,
        fc_index=fc_index,
        player_lookup=players,
    )
    logger.info("team.trade.compared", player_a=player_a, player_b=player_b)
    return result


@router.get("/stats/{player_id}")
async def get_player_stats(
    player_id: str,
    league: League = Depends(get_league_for_user),
    redis: Redis = Depends(get_redis),
    projection: ProjectionService = Depends(get_projection_service),
    sleeper: SleeperClient = Depends(get_sleeper_client),
    weeks: int = Query(default=8, ge=1, le=18),
):
    """Return weekly fantasy point history for a player (TM-13).

    Returns up to 'weeks' most recent regular-season weeks.
    Off-season: returns empty array (Sleeper stats endpoint has no current-season data).
    """
    nfl_state = await _get_nfl_state(redis, sleeper)
    season = nfl_state["season"]
    current_week = int(nfl_state.get("week", 1))
    season_type = nfl_state.get("season_type", "off")

    weekly_pts: list[dict] = []
    if season_type != "off" and current_week > 1:
        for w in range(max(1, current_week - weeks), current_week):
            stats = await projection.get_player_weekly_stats(season, w)
            player_week = stats.get(player_id, {})
            pts = float(player_week.get("pts_ppr", 0) or 0)
            weekly_pts.append({"week": w, "pts": round(pts, 1)})

    career_avg: dict[str, float] = {}
    for prior_season in [str(int(season) - 1), str(int(season) - 2)]:
        season_pts: list[float] = []
        for w in range(1, 19):
            try:
                stats = await projection.get_player_weekly_stats(prior_season, w)
                pw = stats.get(player_id, {})
                if pw:
                    season_pts.append(float(pw.get("pts_ppr", 0) or 0))
            except Exception:
                break
        if season_pts:
            career_avg[prior_season] = round(sum(season_pts) / len(season_pts), 1)

    logger.info("team.stats.fetched", player_id=player_id, week_count=len(weekly_pts))
    return {
        "player_id": player_id,
        "season": season,
        "weekly_pts": weekly_pts,
        "career_avg": career_avg,
        "season_type": season_type,
    }


@router.post("/lineup/apply")
async def apply_lineup(_: User = Depends(get_current_user)):
    """TM-16 placeholder: Apply suggested lineup via host platform API.

    Requires Yahoo or ESPN write scope — deferred to Phase 3+.
    Sleeper does not support lineup writes via their API.
    """
    raise HTTPException(
        status_code=501,
        detail="Lineup apply is not yet supported. This feature requires Yahoo or ESPN with write scope (Phase 3+).",
    )
