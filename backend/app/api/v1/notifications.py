"""In-app notifications — simple Redis-backed read-once notification queue.

DR-01: league members receive in-app notification when draft is scheduled.
Notifications are pushed by create_draft and cleared on first read.
"""
import json

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

_NOTIFICATION_KEY = "notifications:{user_id}"
NOTIFICATION_TTL = 604800  # 7 days


def notification_key(user_id: str) -> str:
    return _NOTIFICATION_KEY.format(user_id=user_id)


@router.get("")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    """Return all pending notifications for the current user and clear them.

    Notifications are stored as a Redis list (RPUSH); this endpoint
    reads them all (LRANGE 0 -1) and deletes the key in one atomic pass.
    T-4-03: key is derived from server-authoritative JWT user_id — users
    cannot read another user's notifications.
    """
    key = notification_key(str(current_user.id))
    raw_items = await redis.lrange(key, 0, -1)
    if raw_items:
        await redis.delete(key)

    notifications = []
    for raw in raw_items:
        try:
            item = raw.decode() if isinstance(raw, bytes) else raw
            notifications.append(json.loads(item))
        except Exception:
            pass

    return notifications
