"""Yahoo Fantasy Sports league import service.

Follows the same fetch-first, write-atomic pattern as league_service.py (LC-08):
  Step 1: Collect ALL Yahoo API data before opening a DB transaction.
  Step 2–4: Write atomically inside begin_nested().

FLEX mapping: Yahoo uses compound slot names (W/R/T, Q/W/R/T) that map to
Sleeper-style FLEX / SUPERFLEX labels.
"""
import json
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey, CacheTTL
from app.core.logging import logger
from app.models.league import League, LeagueMember, Roster, Team
from app.models.user import User
from app.services.player_id_mapper import PlayerIDMapper
from app.services.yahoo_client import YahooClient

YAHOO_STAT_MAP: dict[int, str] = {
    4: "pass_yd",
    5: "pass_td",
    6: "pass_int",
    9: "rush_yd",
    10: "rush_td",
    11: "rec",
    12: "rec_yd",
    13: "rec_td",
    24: "fum_lost",
}

YAHOO_FLEX_MAP: dict[str, str] = {
    "W/R/T": "FLEX",
    "W/R": "FLEX",
    "W/T": "FLEX",
    "Q/W/R/T": "SUPERFLEX",
    "BN": "BN",
    "IR": "IR",
}


def normalize_yahoo_scoring(settings_data: dict) -> dict:
    """Convert Yahoo stat_categories to normalized scoring_rules dict."""
    league_content = settings_data.get("fantasy_content", {}).get("league", [{}, {}])
    league_meta = league_content[0] if len(league_content) > 0 else {}
    league_body = league_content[1] if len(league_content) > 1 else {}

    settings_obj = league_body.get("settings", {})
    stat_cats = settings_obj.get("stat_categories", {}).get("stats", {})

    normalized: dict[str, float] = {}
    unmodeled: list[str] = []

    for key, stat_entry in stat_cats.items():
        if not str(key).isdigit():
            continue
        stat = stat_entry.get("stat", {})
        stat_id = stat.get("stat_id")
        try:
            value = float(stat.get("value", 0))
        except (TypeError, ValueError):
            continue
        if value == 0:
            continue
        if stat_id in YAHOO_STAT_MAP:
            normalized[YAHOO_STAT_MAP[stat_id]] = value
        else:
            unmodeled.append(f"yahoo_stat_{stat_id}")

    # keeper settings live in settings_obj at the second position
    max_keepers = int(settings_obj.get("max_keepers", league_meta.get("max_keepers", 0)))
    keeper_cost_type = int(settings_obj.get("keeper_cost_type", league_meta.get("keeper_cost_type", 0)))

    return {
        "platform_raw": settings_data,
        "normalized": normalized,
        "keeper_settings": {
            "max_keepers": max_keepers,
            "keeper_cost_type": keeper_cost_type,
            "unmodeled_rules": unmodeled,
        },
    }


def normalize_yahoo_roster_format(settings_data: dict) -> dict:
    """Convert Yahoo roster_positions to Sleeper-style positions list."""
    league_content = settings_data.get("fantasy_content", {}).get("league", [{}, {}])
    league_body = league_content[1] if len(league_content) > 1 else {}
    settings_obj = league_body.get("settings", {})
    raw_positions = settings_obj.get("roster_positions", {})

    positions: list[str] = []
    for key, entry in raw_positions.items():
        if not str(key).isdigit():
            continue
        pos = entry.get("roster_position", {})
        pos_type = pos.get("position_type", pos.get("abbreviation", "BN"))
        try:
            count = int(pos.get("count", 1))
        except (TypeError, ValueError):
            count = 1
        normalized = YAHOO_FLEX_MAP.get(pos_type, pos_type)
        positions.extend([normalized] * count)
    return {"positions": positions}


async def import_yahoo_league(
    league_id: str,
    game_key: str,
    current_user: User,
    db: AsyncSession,
    redis: Redis,
    yahoo: YahooClient,
    week: int = 1,
) -> League:
    """Import a Yahoo league into the unified data model.

    MP-01, MP-02: fetch-first, write-atomic (LC-08 equivalent).
    league_id: Yahoo numeric league ID.
    game_key: Yahoo season game key (e.g. "461").
    """
    league_key = f"{game_key}.l.{league_id}"
    logger.info("yahoo.league.import.start", league_key=league_key, user_id=str(current_user.id))

    # Step 1: Fetch ALL data before opening any transaction
    settings_data = await yahoo.get_league_settings(league_key)
    teams_data = await yahoo.get_league_teams(league_key)

    scoring_rules = normalize_yahoo_scoring(settings_data)
    roster_format = normalize_yahoo_roster_format(settings_data)
    keeper_flag = scoring_rules["keeper_settings"]["max_keepers"] > 0

    league_content = settings_data.get("fantasy_content", {}).get("league", [{}])
    league_meta = league_content[0] if league_content else {}
    season = str(league_meta.get("season", "2025"))
    name = league_meta.get("name", f"Yahoo League {league_id}")
    draft_type = "auction" if str(league_meta.get("draft_type", "")).lower() == "auction" else "snake"

    # Step 2–4: Atomic DB writes
    async with db.begin_nested():
        result = await db.execute(
            select(League).where(
                League.host_platform == "yahoo",
                League.host_league_id == league_id,
                League.season == season,
            )
        )
        league = result.scalar_one_or_none()
        if league is None:
            league = League(
                host_platform="yahoo",
                host_league_id=league_id,
                season=season,
                name=name,
                scoring_rules=scoring_rules,
                roster_format=roster_format,
                draft_type=draft_type,
                keeper_flag=keeper_flag,
                dynasty_flag=False,
                last_synced_at=datetime.now(UTC).replace(tzinfo=None),
            )
            db.add(league)
        else:
            league.scoring_rules = scoring_rules
            league.roster_format = roster_format
            league.last_synced_at = datetime.now(UTC).replace(tzinfo=None)
        await db.flush()

        result = await db.execute(
            select(LeagueMember).where(
                LeagueMember.user_id == current_user.id,
                LeagueMember.league_id == league.id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            db.add(LeagueMember(
                user_id=current_user.id,
                league_id=league.id,
                host_team_id=None,
                role="owner",
                connected_at=datetime.now(UTC).replace(tzinfo=None),
            ))

        teams_content = teams_data.get("fantasy_content", {}).get("league", [{}, {}])
        teams_node = teams_content[1].get("teams", {}) if len(teams_content) > 1 else {}
        mapper = PlayerIDMapper()

        for key, team_entry in teams_node.items():
            if not str(key).isdigit():
                continue
            team_parts = team_entry.get("team", [{}])
            team_info_list = team_parts[0] if team_parts else {}
            if isinstance(team_info_list, list):
                team_info: dict = {}
                for item in team_info_list:
                    if isinstance(item, dict):
                        team_info.update(item)
            else:
                team_info = team_info_list if isinstance(team_info_list, dict) else {}

            host_team_id = str(team_info.get("team_id", key))
            team_name = team_info.get("name", f"Team {key}")

            result = await db.execute(
                select(Team).where(
                    Team.league_id == league.id,
                    Team.host_team_id == host_team_id,
                )
            )
            team_obj = result.scalar_one_or_none()
            if team_obj is None:
                team_obj = Team(league_id=league.id, host_team_id=host_team_id, name=team_name)
                db.add(team_obj)
                await db.flush()

            team_key = f"{game_key}.l.{league_id}.t.{host_team_id}"
            roster_data = await yahoo.get_team_roster(team_key, week)

            players_node = (
                roster_data.get("fantasy_content", {})
                .get("team", [{}, {}])[1]
                .get("roster", {})
                .get("0", {})
                .get("players", {})
            )
            players: list[dict] = []
            starters: list[str] = []
            for pk, player_entry in players_node.items():
                if not str(pk).isdigit():
                    continue
                player_parts = player_entry.get("player", [])
                flat: dict = {}
                for part in player_parts:
                    if isinstance(part, dict):
                        flat.update(part)
                    elif isinstance(part, list):
                        for sub in part:
                            if isinstance(sub, dict):
                                flat.update(sub)
                yahoo_id = str(flat.get("player_id", ""))
                sel_pos_list = flat.get("selected_position", [])
                selected_position = (
                    sel_pos_list[1].get("position", "BN")
                    if len(sel_pos_list) > 1
                    else "BN"
                )
                is_starting = selected_position not in ("BN", "IR")
                sleeper_id = await mapper.yahoo_to_sleeper(db, yahoo_id)
                players.append({
                    "yahoo_id": yahoo_id,
                    "sleeper_id": sleeper_id,
                    "selected_position": selected_position,
                    "is_starting": is_starting,
                })
                if is_starting:
                    starters.append(sleeper_id or yahoo_id)

            snapshot = {"players": players, "starters": starters, "settings": {}}
            result = await db.execute(
                select(Roster).where(Roster.team_id == team_obj.id, Roster.week == week)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Roster(
                    team_id=team_obj.id,
                    week=week,
                    snapshot=snapshot,
                    last_synced_at=datetime.now(UTC).replace(tzinfo=None),
                ))
            else:
                existing.snapshot = snapshot
                existing.last_synced_at = datetime.now(UTC).replace(tzinfo=None)

    await redis.set(
        CacheKey.league_settings(str(league.id)),
        json.dumps({"yahoo": True}),
        ex=CacheTTL.LEAGUE_SETTINGS,
    )
    logger.info("yahoo.league.import.complete", league_id=str(league.id))
    return league


async def refresh_yahoo_league(
    league: League,
    current_user: User,
    db: AsyncSession,
    redis: Redis,
    yahoo: YahooClient,
    week: int = 1,
) -> League:
    """Re-sync a Yahoo league already in the DB."""
    return await import_yahoo_league(
        league_id=league.host_league_id,
        game_key="461",
        current_user=current_user,
        db=db,
        redis=redis,
        yahoo=yahoo,
        week=week,
    )
