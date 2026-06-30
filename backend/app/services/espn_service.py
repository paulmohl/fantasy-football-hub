"""ESPN Fantasy league import service.

Follows the same fetch-first, write-atomic pattern as league_service.py (LC-08).

PITFALL 6: ESPN mRoster view returns ALL teams in one response (response["teams"]).
Do NOT re-request per team; iterate response["teams"] directly.
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
from app.services.espn_client import ESPNClient
from app.services.player_id_mapper import PlayerIDMapper

ESPN_STAT_MAP: dict[int, str] = {
    3: "pass_yd",
    4: "pass_td",
    6: "pass_int",
    20: "rush_yd",
    21: "rush_td",
    41: "rec",
    42: "rec_yd",
    43: "rec_td",
    72: "fum_lost",
}

ESPN_SLOT_MAP: dict[int, str] = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "DEF",
    17: "K",
    5: "FLEX",
    23: "FLEX",
    20: "SUPERFLEX",
    24: "BN",
    25: "IR",
}

_BENCH_SLOT_IDS = {24, 25}


def normalize_espn_scoring(league_data: dict) -> dict:
    """Convert ESPN scoringSettings to normalized format matching Yahoo normalization."""
    settings = league_data.get("settings", {})
    scoring_items = settings.get("scoringSettings", {}).get("scoringItems", [])
    normalized: dict[str, float] = {}
    unmodeled: list[str] = []

    for item in scoring_items:
        stat_id = item.get("statId")
        try:
            points = float(item.get("points", 0))
        except (TypeError, ValueError):
            continue
        if points == 0:
            continue
        if stat_id in ESPN_STAT_MAP:
            normalized[ESPN_STAT_MAP[stat_id]] = points
        else:
            unmodeled.append(f"espn_stat_{stat_id}")

    acq = settings.get("acquisitionSettings", {})
    keeper_count = int(acq.get("keeperCount", 0))
    keeper_order_type = int(acq.get("keeperOrderType", 0))

    return {
        "platform_raw": league_data,
        "normalized": normalized,
        "keeper_settings": {
            "max_keepers": keeper_count,
            "keeper_cost_type": keeper_order_type,
            "unmodeled_rules": unmodeled,
        },
    }


def normalize_espn_roster_format(league_data: dict) -> dict:
    """Convert ESPN lineupSlotCounts to Sleeper-style positions list."""
    slot_counts = (
        league_data.get("settings", {})
        .get("rosterSettings", {})
        .get("lineupSlotCounts", {})
    )
    positions: list[str] = []
    for slot_id_str, count in slot_counts.items():
        try:
            slot_id = int(slot_id_str)
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count == 0:
            continue
        pos = ESPN_SLOT_MAP.get(slot_id, f"SLOT_{slot_id}")
        positions.extend([pos] * count)
    return {"positions": positions}


async def import_espn_league(
    league_id: str,
    year: int,
    is_public: bool,
    current_user: User,
    db: AsyncSession,
    redis: Redis,
    espn: ESPNClient,
    week: int = 1,
) -> League:
    """Import an ESPN league into the unified data model.

    MP-03, MP-04, MP-05: fetch-first, write-atomic (LC-08 equivalent).
    Public leagues: is_public=True sets LeagueMember.role="viewer".
    """
    logger.info(
        "espn.league.import.start",
        league_id=league_id,
        year=year,
        is_public=is_public,
        user_id=str(current_user.id),
    )

    # Step 1: Fetch all data before opening any transaction
    league_data = await espn.get_league(league_id, year)
    scoring_rules = normalize_espn_scoring(league_data)
    roster_format = normalize_espn_roster_format(league_data)
    keeper_flag = scoring_rules["keeper_settings"]["max_keepers"] > 0

    settings_obj = league_data.get("settings", {})
    name = settings_obj.get("name", f"ESPN League {league_id}")
    season = str(year)
    draft_type = (
        "auction"
        if settings_obj.get("draftSettings", {}).get("type") == "AUCTION"
        else "snake"
    )

    # Step 2–4: Atomic DB writes
    async with db.begin_nested():
        result = await db.execute(
            select(League).where(
                League.host_platform == "espn",
                League.host_league_id == league_id,
                League.season == season,
            )
        )
        league = result.scalar_one_or_none()
        if league is None:
            league = League(
                host_platform="espn",
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
        role = "viewer" if is_public else "owner"
        if member is None:
            db.add(LeagueMember(
                user_id=current_user.id,
                league_id=league.id,
                host_team_id=None,
                role=role,
                connected_at=datetime.now(UTC).replace(tzinfo=None),
            ))

        mapper = PlayerIDMapper()
        # Pitfall 6: mRoster returns ALL teams in league_data["teams"]
        for team_obj_data in league_data.get("teams", []):
            host_team_id = str(team_obj_data.get("id", ""))
            team_name = f"{team_obj_data.get('location', '')} {team_obj_data.get('nickname', '')}".strip()
            if not team_name:
                team_name = f"Team {host_team_id}"

            result = await db.execute(
                select(Team).where(
                    Team.league_id == league.id,
                    Team.host_team_id == host_team_id,
                )
            )
            team = result.scalar_one_or_none()
            if team is None:
                team = Team(league_id=league.id, host_team_id=host_team_id, name=team_name)
                db.add(team)
                await db.flush()

            roster_entries = team_obj_data.get("roster", {}).get("entries", [])
            players: list[dict] = []
            starters: list[str] = []
            for entry in roster_entries:
                espn_id = str(entry.get("playerId", ""))
                lineup_slot_id = entry.get("lineupSlotId", 24)
                is_starting = lineup_slot_id not in _BENCH_SLOT_IDS
                sleeper_id = await mapper.espn_to_sleeper(db, espn_id)
                players.append({
                    "espn_id": espn_id,
                    "sleeper_id": sleeper_id,
                    "lineup_slot_id": lineup_slot_id,
                    "is_starting": is_starting,
                })
                if is_starting:
                    starters.append(sleeper_id or espn_id)

            snapshot = {"players": players, "starters": starters, "settings": {}}
            result = await db.execute(
                select(Roster).where(Roster.team_id == team.id, Roster.week == week)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Roster(
                    team_id=team.id,
                    week=week,
                    snapshot=snapshot,
                    last_synced_at=datetime.now(UTC).replace(tzinfo=None),
                ))
            else:
                existing.snapshot = snapshot
                existing.last_synced_at = datetime.now(UTC).replace(tzinfo=None)

    await redis.set(
        CacheKey.league_settings(str(league.id)),
        json.dumps({"espn": True}),
        ex=CacheTTL.LEAGUE_SETTINGS,
    )
    logger.info("espn.league.import.complete", league_id=str(league.id), is_public=is_public)
    return league
