"""arq background tasks for Fantasy Football Hub.

Phase 2 additions:
  - fantasycalc_prewarm: Pre-warm FantasyCalc values cache at midnight UTC
    so the first user request of the day hits Redis, not FantasyCalc.

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


class WorkerSettings:
    """arq worker configuration.

    Run: arq workers.tasks.WorkerSettings
    """

    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    functions = [fantasycalc_prewarm]
    cron_jobs = [
        cron(fantasycalc_prewarm, hour=0, minute=5, name="fantasycalc_prewarm_nightly"),
    ]
