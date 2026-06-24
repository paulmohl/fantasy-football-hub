"""League import and refresh service.

CRITICAL ORDERING RULE (LC-08):
  Collect ALL Sleeper API responses before opening a DB transaction.
  If any API call fails, the transaction never opens and no partial state is written.

DEDUP RULE (LC-10):
  leagues table has UNIQUE(host_platform, host_league_id, season).
  We use select-then-insert-or-update so tests can run against SQLite.
  Production behavior is identical; uniqueness is enforced by the DB constraint.

FRESH CONNECT RULE (LC-12):
  Re-connecting a previously disconnected league is treated as a fresh import.
  league_members row was deleted on disconnect — a new one is inserted here.
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
from app.services.sleeper_client import SleeperClient


def classify_draft(league_data: dict) -> str:
    """Classify Sleeper draft type from league.settings.

    Sleeper's 'type' field in settings maps directly to our draft_type enum.
    Fallback to 'snake' for any unrecognized value.
    """
    settings = league_data.get("settings", {})
    raw_type = settings.get("type", "snake")
    valid = {"snake", "auction", "linear", "third_round_reversal"}
    return raw_type if raw_type in valid else "snake"


def _keeper_flag(league_data: dict) -> bool:
    settings = league_data.get("settings", {})
    return int(settings.get("num_keepers", 0)) > 0


def _dynasty_flag(league_data: dict) -> bool:
    settings = league_data.get("settings", {})
    return settings.get("type") == "dynasty"


async def import_league(
    league_id: str,
    current_user: User,
    db: AsyncSession,
    redis: Redis,
    sleeper: SleeperClient,
    week: int = 1,
) -> League:
    """Import a Sleeper league for the current user.

    Step 1: Collect all Sleeper data (any failure aborts before DB touches).
    Step 2: Upsert league row (dedup by host key).
    Step 3: Upsert league_members row.
    Step 4: Upsert team + roster rows.
    Step 5: Cache league settings.
    """
    logger.info("league.import.start", league_id=league_id, user_id=str(current_user.id))

    # Step 1: Fetch all data from Sleeper BEFORE opening a transaction (LC-08)
    league_data = await sleeper.get_league(league_id)
    rosters = await sleeper.get_rosters(league_id)
    members = await sleeper.get_users(league_id)

    # Step 2–4: All DB writes in one atomic savepoint.
    # begin_nested() works whether or not an outer transaction is already open,
    # making this callable from both HTTP handlers and test fixtures.
    async with db.begin_nested():
        # League upsert (LC-10 dedup)
        result = await db.execute(
            select(League).where(
                League.host_platform == "sleeper",
                League.host_league_id == league_id,
                League.season == league_data["season"],
            )
        )
        league = result.scalar_one_or_none()
        scoring_rules = league_data.get("scoring_settings") or {}
        roster_format = {"positions": league_data.get("roster_positions") or []}

        if league is None:
            league = League(
                host_platform="sleeper",
                host_league_id=league_id,
                season=league_data["season"],
                name=league_data["name"],
                scoring_rules=scoring_rules,
                roster_format=roster_format,
                draft_type=classify_draft(league_data),
                keeper_flag=_keeper_flag(league_data),
                dynasty_flag=_dynasty_flag(league_data),
                last_synced_at=datetime.now(UTC),
            )
            db.add(league)
        else:
            league.name = league_data["name"]
            league.scoring_rules = scoring_rules
            league.roster_format = roster_format
            league.last_synced_at = datetime.now(UTC)
        await db.flush()

        # Find current user's roster_id from rosters list
        member_host_team_id = None
        for roster in rosters:
            if roster.get("owner_id") == str(current_user.id):
                member_host_team_id = str(roster["roster_id"])
                break

        # LeagueMember upsert (LC-10, LC-12)
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
                host_team_id=member_host_team_id,
                role="owner",
                connected_at=datetime.now(UTC),
            ))
        else:
            member.host_team_id = member_host_team_id

        # Teams + rosters upsert
        for roster in rosters:
            host_team_id = str(roster["roster_id"])

            result = await db.execute(
                select(Team).where(
                    Team.league_id == league.id,
                    Team.host_team_id == host_team_id,
                )
            )
            team = result.scalar_one_or_none()
            if team is None:
                team = Team(
                    league_id=league.id,
                    host_team_id=host_team_id,
                    name=None,
                    owner_user_id=None,
                )
                db.add(team)
                await db.flush()

            snapshot_data = {
                "starters": roster.get("starters") or [],
                "players": roster.get("players") or [],
                "settings": roster.get("settings") or {},
            }
            result = await db.execute(
                select(Roster).where(
                    Roster.team_id == team.id,
                    Roster.week == week,
                )
            )
            existing_roster = result.scalar_one_or_none()
            if existing_roster is None:
                db.add(Roster(
                    team_id=team.id,
                    week=week,
                    snapshot=snapshot_data,
                    last_synced_at=datetime.now(UTC),
                ))
            else:
                existing_roster.snapshot = snapshot_data
                existing_roster.last_synced_at = datetime.now(UTC)

    # Step 5: Cache after successful savepoint commit (outside transaction)
    await redis.set(
        CacheKey.league_settings(str(league.id)),
        json.dumps(league_data),
        ex=CacheTTL.LEAGUE_SETTINGS,
    )
    await redis.set(
        CacheKey.league_members(str(league.id)),
        json.dumps(members),
        ex=CacheTTL.LEAGUE_MEMBERS,
    )
    logger.info("league.import.complete", league_id=str(league.id))
    return league


async def refresh_league(
    league: League,
    db: AsyncSession,
    redis: Redis,
    sleeper: SleeperClient,
    week: int = 1,
) -> League:
    """Re-fetch league data from Sleeper and update Postgres + cache (LC-07)."""
    logger.info("league.refresh.start", league_id=str(league.id))
    league_data = await sleeper.get_league(league.host_league_id)
    rosters = await sleeper.get_rosters(league.host_league_id)
    members = await sleeper.get_users(league.host_league_id)

    async with db.begin_nested():
        league.scoring_rules = league_data.get("scoring_settings") or {}
        league.roster_format = {"positions": league_data.get("roster_positions") or []}
        league.draft_type = classify_draft(league_data)
        league.keeper_flag = _keeper_flag(league_data)
        league.dynasty_flag = _dynasty_flag(league_data)
        league.last_synced_at = datetime.now(UTC)

        for roster in rosters:
            host_team_id = str(roster["roster_id"])
            result = await db.execute(
                select(Team)
                .where(Team.league_id == league.id)
                .where(Team.host_team_id == host_team_id)
            )
            team = result.scalar_one_or_none()
            if team:
                roster_result = await db.execute(
                    select(Roster)
                    .where(Roster.team_id == team.id)
                    .where(Roster.week == week)
                )
                existing_roster = roster_result.scalar_one_or_none()
                if existing_roster:
                    existing_roster.snapshot = {
                        "starters": roster.get("starters") or [],
                        "players": roster.get("players") or [],
                        "settings": roster.get("settings") or {},
                    }
                    existing_roster.last_synced_at = datetime.now(UTC)

    # Invalidate and repopulate cache
    await redis.delete(CacheKey.league_settings(str(league.id)))
    await redis.delete(CacheKey.league_members(str(league.id)))
    await redis.set(
        CacheKey.league_settings(str(league.id)),
        json.dumps(league_data),
        ex=CacheTTL.LEAGUE_SETTINGS,
    )
    await redis.set(
        CacheKey.league_members(str(league.id)),
        json.dumps(members),
        ex=CacheTTL.LEAGUE_MEMBERS,
    )
    logger.info("league.refresh.complete", league_id=str(league.id))
    return league
