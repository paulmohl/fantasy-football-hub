"""arq background tasks for Fantasy Football Hub.

Phase 2 additions:
  - fantasycalc_prewarm: Pre-warm FantasyCalc values cache at midnight UTC
    so the first user request of the day hits Redis, not FantasyCalc.

Phase 3 additions:
  - seed_player_cross_map: Download ffb_ids CSV and bulk-upsert player cross-map weekly.

Task registry: add all tasks to the WorkerSettings.functions list.
"""
import json
import os

import httpx
from arq.connections import RedisSettings
from arq.cron import cron
from redis.asyncio import Redis

from app.core.cache import CacheKey, CacheTTL
from app.core.logging import logger

FANTASYCALC_BASE = "https://api.fantasycalc.com"


async def fantasycalc_prewarm(ctx: dict) -> None:
    """Pre-warm FantasyCalc redraft and dynasty values into Redis.

    Scheduled: nightly at 00:05 UTC via arq cron.
    Uses verified URL: /values/current with isDynasty param (CONTEXT.md DECISION-001).
    """
    redis: Redis = ctx["redis"]
    async with httpx.AsyncClient(timeout=20.0) as client:
        for is_dynasty in (False, True):
            key = CacheKey.fantasycalc_values(is_dynasty)
            try:
                r = await client.get(
                    f"{FANTASYCALC_BASE}/values/current",
                    params={
                        "isDynasty": str(is_dynasty).lower(),
                        "numQbs": 1,
                        "numTeams": 12,
                        "ppr": 1,
                    },
                )
                r.raise_for_status()
                data = r.json()
                await redis.set(key, json.dumps(data), ex=CacheTTL.FANTASYCALC)
                logger.info("fantasycalc.prewarm.ok", is_dynasty=is_dynasty, count=len(data))
            except Exception as exc:
                logger.error("fantasycalc.prewarm.failed", is_dynasty=is_dynasty, error=str(exc))


async def seed_player_cross_map(ctx: dict) -> None:
    """Download ffb_ids CSV and bulk-upsert into player_cross_map table.

    Scheduled: weekly on Monday at 02:00 UTC.
    Also callable on-demand via arq enqueue for Phase 3 initial deployment.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.data.player_cross_map_seed import FFB_IDS_URL, FALLBACK_URL, load_player_cross_map_from_csv

    csv_text = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in (FFB_IDS_URL, FALLBACK_URL):
            try:
                r = await client.get(url)
                r.raise_for_status()
                csv_text = r.text
                break
            except Exception as exc:
                logger.warning("player_cross_map.seed.download_failed", url=url, error=str(exc))

    if not csv_text:
        logger.error("player_cross_map.seed.all_urls_failed")
        return

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        async with db.begin():
            count = await load_player_cross_map_from_csv(csv_text, db)
    await engine.dispose()
    logger.info("player_cross_map.seed.task_complete", rows_upserted=count)


async def check_platform_credentials(ctx: dict) -> None:
    """MP-06: Validate all stored platform credentials; mark unhealthy on auth failure.

    Scheduled every 6 hours. For Yahoo: calls get_game_key with current token.
    For ESPN private: calls get_league_settings. Sets is_healthy=False on auth error.
    """
    import base64
    import json as _json

    from sqlalchemy import select as _select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker as _sessionmaker

    from app.core.config import settings as _settings
    from app.models.credential import UserCredential
    from app.models.user import User
    from app.services.credential_service import CredentialService
    from app.services.espn_client import ESPNAuthExpired, ESPNClient
    from app.services.yahoo_client import YahooAuthExpired, YahooClient

    engine = create_async_engine(_settings.database_url)
    _SessionLocal = _sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    cred_svc = CredentialService()

    async with _SessionLocal() as db:
        result = await db.execute(
            _select(UserCredential, User)
            .join(User, UserCredential.user_id == User.id)
            .where(UserCredential.is_healthy == True)  # noqa: E712
        )
        rows = result.all()

    for cred_row, user_row in rows:
        try:
            decrypted = _json.loads(cred_svc.decrypt(user_row, cred_row.credentials_encrypted))
        except Exception as exc:
            logger.error(
                "credential.check.decrypt_failed",
                user_id=str(user_row.id),
                platform=cred_row.platform,
                error=str(exc),
            )
            async with _SessionLocal() as db:
                async with db.begin():
                    await cred_svc.mark_unhealthy(user_row.id, cred_row.platform, db)
            continue

        is_healthy = True
        async with httpx.AsyncClient(timeout=10.0) as http:
            if cred_row.platform == "yahoo":
                try:
                    yahoo = YahooClient(http, decrypted.get("access_token", ""))
                    await yahoo.get_game_key()
                except YahooAuthExpired:
                    is_healthy = False
                except Exception as exc:
                    logger.warning(
                        "credential.check.yahoo_error",
                        user_id=str(user_row.id),
                        error=str(exc),
                    )
            elif cred_row.platform == "espn":
                if not decrypted.get("is_public", False):
                    espn = ESPNClient(
                        http,
                        swid=decrypted.get("swid"),
                        espn_s2=decrypted.get("espn_s2"),
                    )
                    league_id = decrypted.get("league_id", decrypted.get("swid", "1"))
                    try:
                        await espn.get_league_settings(str(league_id), _settings.nfl_season_year)
                    except ESPNAuthExpired:
                        is_healthy = False
                    except Exception as exc:
                        logger.warning(
                            "credential.check.espn_error",
                            user_id=str(user_row.id),
                            error=str(exc),
                        )

        if not is_healthy:
            async with _SessionLocal() as db:
                async with db.begin():
                    await cred_svc.mark_unhealthy(user_row.id, cred_row.platform, db)
            logger.info(
                "credential.marked_unhealthy",
                user_id=str(user_row.id),
                platform=cred_row.platform,
            )

    await engine.dispose()


async def auto_draft_pick(ctx: dict, draft_id: str, pick_num: int) -> None:
    """Auto-draft pick when clock expires (DR-08, D-04).

    T-4-05 Idempotent guard: checks draft.current_pick_num in Redis before acting.
    If pick_num != current_pick_num + 1, another pick was made — exit silently.
    _job_id=f"autodraft:{draft_id}:{pick_num}" prevents collision across picks (via arm_auto_draft_timer).
    """
    redis = ctx.get("redis")
    if not redis:
        return

    from app.core.cache import CacheKey as _CK

    # T-4-05 Idempotent guard: verify this pick is still outstanding
    current_raw = await redis.get(_CK.draft_current_pick(draft_id))
    current_pick = int(
        current_raw.decode() if isinstance(current_raw, bytes) else (current_raw or 0)
    )
    if current_pick != pick_num - 1:
        logger.info(
            "draft.auto_draft.stale",
            draft_id=draft_id,
            pick_num=pick_num,
            current=current_pick,
        )
        return  # Pick already made by human or another auto-draft job

    # Check draft is still live
    state_raw = await redis.get(_CK.draft_state(draft_id))
    state = (state_raw.decode() if isinstance(state_raw, bytes) else state_raw) or ""
    if state != "live":
        return

    import json as _json
    import time as _time
    from uuid import UUID

    from sqlalchemy import select as _select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import settings as _settings
    from app.models.draft import Draft, DraftPick, DraftQueue
    from app.models.league import Team
    from app.services.draft_service import (
        arm_auto_draft_timer,
        record_draft_event,
        select_auto_draft_player,
        snake_pick_to_slot,
    )

    engine = create_async_engine(_settings.database_url)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        draft_result = await db.execute(_select(Draft).where(Draft.id == UUID(draft_id)))
        draft = draft_result.scalar_one_or_none()
        if not draft or draft.status != "live":
            await engine.dispose()
            return

        _, team_slot = snake_pick_to_slot(pick_num, draft.num_teams)
        team_id = draft.draft_order[team_slot] if draft.draft_order else None
        if not team_id:
            await engine.dispose()
            return

        # Load user's queue for this team
        team_result = await db.execute(_select(Team).where(Team.id == UUID(str(team_id))))
        team = team_result.scalar_one_or_none()
        user_id = str(team.owner_user_id) if team else None

        user_queue: list[str] = []
        if user_id:
            queue_result = await db.execute(
                _select(DraftQueue)
                .where(
                    DraftQueue.draft_id == UUID(draft_id),
                    DraftQueue.user_id == UUID(user_id),
                )
                .order_by(DraftQueue.position)
            )
            user_queue = [q.player_id for q in queue_result.scalars()]

        # Load ADP rankings from Redis (FantasyCalc)
        fc_raw = await redis.get(_CK.fantasycalc_values(False))
        adp_players: list[dict] = []
        if fc_raw:
            try:
                fc_data = _json.loads(fc_raw.decode() if isinstance(fc_raw, bytes) else fc_raw)
                adp_players = [
                    {
                        "player_id": str(
                            e.get("player", {}).get("sleeperId", "")
                            or e.get("sleeperId", "")
                        ),
                        "overall_rank": e.get("overallRank", 9999),
                        "position": (
                            e.get("player", {}).get("position", "")
                            or e.get("position", "")
                        ),
                    }
                    for e in fc_data
                    if e.get("player", {}).get("sleeperId") or e.get("sleeperId")
                ]
            except Exception:
                pass

        # team_positions: positions already on this team's roster (from picks so far)
        picks_result = await db.execute(
            _select(DraftPick).where(
                DraftPick.draft_id == UUID(draft_id),
                DraftPick.team_id == UUID(str(team_id)),
            )
        )
        team_positions: list[str] = []  # position data requires player lookup; simplified here
        roster_format: dict = {}         # Commissioner may configure in league settings

        best_player = await select_auto_draft_player(
            redis, draft_id, user_queue, adp_players, team_positions, roster_format
        )
        if not best_player:
            await engine.dispose()
            return

        round_num, _ = snake_pick_to_slot(pick_num, draft.num_teams)

        async with db.begin_nested():
            pick = DraftPick(
                draft_id=UUID(draft_id),
                pick_num=pick_num,
                round=round_num,
                team_id=UUID(str(team_id)),
                player_id=best_player,
                is_auto_pick=True,
            )
            db.add(pick)
            draft.current_pick_num = pick_num
            await db.flush()
        await db.commit()

    # Remove from available SET and update current pick counter
    available_key = _CK.draft_available(draft_id)
    await redis.srem(available_key, best_player)
    await redis.set(_CK.draft_current_pick(draft_id), str(pick_num))

    # New deadline for the next pick
    deadline = _time.time() + draft.pick_clock_seconds
    await redis.set(
        _CK.draft_deadline(draft_id),
        str(deadline),
        ex=draft.pick_clock_seconds + 30,
    )

    event_id = await record_draft_event(redis, draft_id, "auto_drafted", {
        "pick_num": str(pick_num),
        "player_id": best_player,
        "team_id": str(team_id),
        "round": str(round_num),
    })

    # B3: Emit auto_drafted event to Socket.IO room from arq worker via AsyncRedisManager
    import socketio as _sio
    next_pick = pick_num + 1
    pick_payload = {
        "pick": {
            "pick_num": pick_num,
            "player_id": best_player,
            "team_id": str(team_id),
            "round": round_num,
            "is_auto_pick": True,
            "event_id": event_id,
        },
        "next_pick_num": next_pick,
        "deadline": deadline,
    }
    from app.core.config import settings as _cfg
    external_sio = _sio.AsyncRedisManager(_cfg.redis_url, write_only=True)
    await external_sio.emit("auto_drafted", pick_payload, room=f"draft:{draft_id}", namespace="/draft")
    # Also broadcast new deadline so all clients update PickClock
    await external_sio.emit(
        "pick_deadline_sync",
        {"deadline": deadline, "pick_num": next_pick},
        room=f"draft:{draft_id}",
        namespace="/draft",
    )

    # B5: Detect final pick → transition to recap; otherwise arm next auto-draft timer
    total_picks = draft.num_teams * draft.num_rounds
    if pick_num >= total_picks:
        await redis.set(f"draft:{draft_id}:status", "complete")
        await external_sio.emit(
            "draft_complete",
            {"draft_id": draft_id},
            room=f"draft:{draft_id}",
            namespace="/draft",
        )
        from arq import create_pool
        from arq.connections import RedisSettings as _RS
        arq_pool_recap = await create_pool(_RS.from_dsn(_cfg.redis_url))
        await arq_pool_recap.enqueue_job("post_draft_recap", draft_id)
        await arq_pool_recap.aclose()
    else:
        await arm_auto_draft_timer(
            ctx.get("redis_pool") or redis, draft_id, next_pick, deadline
        )

    logger.info(
        "draft.auto_draft.complete",
        draft_id=draft_id,
        pick_num=pick_num,
        player_id=best_player,
    )
    await engine.dispose()


async def post_draft_recap(ctx: dict, draft_id: str) -> None:
    """Compute ADP grades after the last pick and set Draft.status = complete (DR-14)."""
    logger.info("draft.recap.start", draft_id=draft_id)

    redis = ctx.get("redis")
    if not redis:
        return

    import json as _json
    from uuid import UUID

    from sqlalchemy import select as _select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.cache import CacheKey as _CK
    from app.core.config import settings as _settings
    from app.models.draft import Draft, DraftPick
    from app.services.draft_service import compute_adp_grades, record_draft_event

    engine = create_async_engine(_settings.database_url)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        draft_result = await db.execute(_select(Draft).where(Draft.id == UUID(draft_id)))
        draft = draft_result.scalar_one_or_none()
        if not draft:
            await engine.dispose()
            return

        picks_result = await db.execute(
            _select(DraftPick).where(DraftPick.draft_id == UUID(draft_id))
        )
        all_picks = list(picks_result.scalars())

        picks_by_team: dict[str, list[dict]] = {}
        for pick in all_picks:
            tid = str(pick.team_id)
            if tid not in picks_by_team:
                picks_by_team[tid] = []
            picks_by_team[tid].append({"player_id": pick.player_id, "pick_num": pick.pick_num})

        # ADP from cached FantasyCalc values
        fc_raw = await redis.get(_CK.fantasycalc_values(False))
        adp_lookup: dict[str, float] = {}
        if fc_raw:
            try:
                fc_data = _json.loads(fc_raw.decode() if isinstance(fc_raw, bytes) else fc_raw)
                for e in fc_data:
                    pid = str(
                        e.get("player", {}).get("sleeperId", "")
                        or e.get("sleeperId", "")
                    )
                    if pid:
                        adp_lookup[pid] = float(e.get("overallRank", 9999))
            except Exception:
                pass

        grades = compute_adp_grades(picks_by_team, adp_lookup)

        async with db.begin_nested():
            draft.status = "complete"
            await db.flush()
        await db.commit()

    await redis.set(_CK.draft_state(draft_id), "complete")
    await record_draft_event(redis, draft_id, "draft_complete", {"grades": _json.dumps(grades)})
    logger.info("draft.recap.complete", draft_id=draft_id, teams_graded=len(grades))
    await engine.dispose()


class WorkerSettings:
    """arq worker configuration.

    Run: arq workers.tasks.WorkerSettings
    """

    redis_settings = RedisSettings.from_dsn(
        (os.environ.get("REDIS_URL") or "redis://localhost:6379/0").replace("rediss://", "redis://", 1),
        ssl=os.environ.get("REDIS_URL", "").startswith("rediss://"),
    )
    functions = [
        fantasycalc_prewarm,
        seed_player_cross_map,
        check_platform_credentials,
        auto_draft_pick,   # Phase 4: auto-draft pick on clock expiry (DR-08, T-4-05)
        post_draft_recap,  # Phase 4: compute grades after final pick (DR-14)
    ]
    cron_jobs = [
        cron(fantasycalc_prewarm, hour=0, minute=5, name="fantasycalc_prewarm_nightly"),
        cron(seed_player_cross_map, weekday=0, hour=2, minute=0, name="player_cross_map_weekly"),
        cron(check_platform_credentials, hour={0, 6, 12, 18}, minute=30, name="credential_health_check"),
    ]
