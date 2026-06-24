"""arq background worker: purge cached league data 30 days after disconnect.

LC-11: Historical cached data is retained for 30 days then purged.
This job is enqueued by the DELETE /leagues/{id}/connection endpoint.
"""
from app.core.logging import logger


async def purge_league_cache(ctx, league_id: str) -> None:
    """Delete all Redis cache keys for a disconnected league.

    Keys purged: league:{id}:settings, league:{id}:members, league:{id}:rosters:*
    """
    redis = ctx.get("redis")
    if not redis:
        logger.error("league_purge.no_redis", league_id=league_id)
        return

    pattern = f"league:{league_id}:*"
    cursor = 0
    deleted = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        if keys:
            deleted += await redis.delete(*keys)
        if cursor == 0:
            break

    logger.info("league_purge.complete", league_id=league_id, keys_deleted=deleted)


class WorkerSettings:
    """arq worker configuration for the league purge job."""
    functions = [purge_league_cache]
    queue_name = "arq:default"
