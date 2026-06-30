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


class WorkerSettings:
    """arq worker configuration.

    Run: arq workers.tasks.WorkerSettings
    """

    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    functions = [fantasycalc_prewarm, seed_player_cross_map, check_platform_credentials]
    cron_jobs = [
        cron(fantasycalc_prewarm, hour=0, minute=5, name="fantasycalc_prewarm_nightly"),
        cron(seed_player_cross_map, weekday=0, hour=2, minute=0, name="player_cross_map_weekly"),
        cron(check_platform_credentials, hour={0, 6, 12, 18}, minute=30, name="credential_health_check"),
    ]
