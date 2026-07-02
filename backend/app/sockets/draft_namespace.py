"""Socket.IO /draft namespace — real-time draft event bus.

CRITICAL: Registered via sio.register_namespace(DraftNamespace('/draft')) in main.py
at MODULE LEVEL, before socketio.ASGIApp(sio, ...) is constructed.

Security model:
- T-4-01: team_id ALWAYS derived from auth session (user_id → Team.owner_user_id); never from client
- T-4-04: Commissioner role verified on EVERY privileged event (pause, resume, end_draft, set_order)
- T-4-03: Redis stream written server-side only; no client endpoint touches XADD
"""
import time
from uuid import UUID

import socketio
from sqlalchemy import select

from app.core.cache import CacheKey
from app.core.database import SessionLocal
from app.core.logging import logger
from app.core.security import decode_token
from app.models.draft import Draft, DraftChatMessage, DraftPick, DraftQueue
from app.models.league import Team
from app.services.draft_service import (
    arm_auto_draft_timer,
    record_draft_event,
    replay_since,
    snake_pick_to_slot,
)


class DraftNamespace(socketio.AsyncNamespace):
    """Handles all Socket.IO events for the /draft namespace.

    Session storage (per SID):
        user_id: str  — authenticated user UUID
        draft_id: str — draft UUID this client is connected to
        team_id: str | None — this user's team_id in the draft (resolved on connect)
    """

    async def on_connect(self, sid: str, environ: dict, auth: dict | None = None) -> None:
        """Validate JWT + draft membership; add client to draft room."""
        if not auth or not auth.get("token"):
            raise socketio.exceptions.ConnectionRefusedError("auth_required")
        user_id = decode_token(auth["token"])
        if not user_id:
            raise socketio.exceptions.ConnectionRefusedError("invalid_token")
        draft_id = auth.get("draft_id")
        if not draft_id:
            raise socketio.exceptions.ConnectionRefusedError("draft_id_required")

        # Resolve team_id from DB using owner_user_id (T-4-01: never trust client)
        team_id: str | None = None
        async with SessionLocal() as db:
            draft_result = await db.execute(
                select(Draft).where(Draft.id == UUID(draft_id))
            )
            draft = draft_result.scalar_one_or_none()
            if not draft:
                raise socketio.exceptions.ConnectionRefusedError("draft_not_found")
            # Find this user's Team in the draft's league via owner_user_id
            team_result = await db.execute(
                select(Team).where(
                    Team.league_id == draft.league_id,
                    Team.owner_user_id == UUID(user_id),
                )
            )
            team = team_result.scalar_one_or_none()
            if team:
                team_id = str(team.id)

        await self.save_session(sid, {
            "user_id": user_id,
            "draft_id": draft_id,
            "team_id": team_id,
        })
        await self.enter_room(sid, f"draft:{draft_id}")
        logger.info("draft.connect", sid=sid, user_id=user_id, draft_id=draft_id)

        # Announce presence to other room members
        await self.emit(
            "member_presence",
            {"user_id": user_id, "online": True},
            room=f"draft:{draft_id}",
            skip_sid=sid,
        )

    async def on_disconnect(self, sid: str, reason: str = "") -> None:
        session = await self.get_session(sid)
        if not session:
            return
        await self.emit(
            "member_presence",
            {"user_id": session["user_id"], "online": False},
            room=f"draft:{session['draft_id']}",
            skip_sid=sid,
        )
        logger.info("draft.disconnect", sid=sid, user_id=session["user_id"])

    async def on_pick(self, sid: str, data: dict) -> dict:
        """Submit a player pick.

        T-4-01: team_id from session (auth), not from data.
        Validates: correct turn, player available, pick lock acquired.
        """
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        team_id = session.get("team_id")
        player_id = str(data.get("player_id", ""))

        if not team_id or not player_id:
            return {"ok": False, "error": "invalid_request"}

        from app.core.redis import get_redis
        redis = await get_redis()

        # Acquire pick lock (SETNX, 5-second TTL — prevents double submissions)
        lock_key = CacheKey.draft_lock(draft_id)
        acquired = await redis.set(lock_key, sid, nx=True, ex=5)
        if not acquired:
            return {"ok": False, "error": "pick_in_flight"}

        try:
            # Validate player is available BEFORE opening DB transaction (T-4-03 pattern)
            available_key = CacheKey.draft_available(draft_id)
            if not await redis.sismember(available_key, player_id):
                return {"ok": False, "error": "player_not_available"}

            async with SessionLocal() as db:
                # Load draft state
                draft_result = await db.execute(select(Draft).where(Draft.id == UUID(draft_id)))
                draft = draft_result.scalar_one_or_none()
                if not draft or draft.status != "live":
                    return {"ok": False, "error": "draft_not_live"}

                # Validate it's this team's turn (T-4-01: derived server-side)
                pick_num = draft.current_pick_num + 1
                round_num, team_slot = snake_pick_to_slot(pick_num, draft.num_teams)
                expected_team_id = draft.draft_order[team_slot] if draft.draft_order else None
                if str(expected_team_id) != team_id:
                    return {"ok": False, "error": "not_your_turn"}

                # Insert DraftPick and advance current_pick_num
                async with db.begin_nested():
                    pick = DraftPick(
                        draft_id=UUID(draft_id),
                        pick_num=pick_num,
                        round=round_num,
                        team_id=UUID(team_id),
                        player_id=player_id,
                        is_auto_pick=False,
                    )
                    db.add(pick)
                    draft.current_pick_num = pick_num
                    await db.flush()

                await db.commit()

            # Update Redis: remove from available set, update current_pick counter
            await redis.srem(available_key, player_id)
            await redis.set(CacheKey.draft_current_pick(draft_id), str(pick_num))

            # Set next pick deadline (server-authoritative per D-03)
            deadline = time.time() + draft.pick_clock_seconds
            await redis.set(
                CacheKey.draft_deadline(draft_id),
                str(deadline),
                ex=draft.pick_clock_seconds + 30,
            )

            # Record in stream (T-4-03: server-side only, AFTER DB commit)
            event_id = await record_draft_event(redis, draft_id, "pick_confirmed", {
                "pick_num": str(pick_num),
                "player_id": player_id,
                "team_id": team_id,
                "round": str(round_num),
                "is_auto_pick": "false",
            })

            # Emit pick to all room participants
            pick_data = {
                "pick_num": pick_num,
                "player_id": player_id,
                "team_id": team_id,
                "round": round_num,
                "is_auto_pick": False,
                "event_id": event_id,
            }
            await self.emit("pick_confirmed", pick_data, room=f"draft:{draft_id}")

            # Broadcast new pick deadline so all clients update PickClock (D-03/B4)
            next_pick_num = pick_num + 1
            await self.emit(
                "pick_deadline_sync",
                {"deadline": deadline, "pick_num": next_pick_num},
                room=f"draft:{draft_id}",
            )

            # Detect final pick → transition to recap; otherwise arm auto-draft timer (B5)
            total_picks = draft.num_teams * draft.num_rounds
            if pick_num >= total_picks:
                await self.emit("draft_complete", {"draft_id": draft_id}, room=f"draft:{draft_id}")
                try:
                    import arq
                    from app.core.config import settings as _settings
                    arq_pool = await arq.create_pool(
                        arq.connections.RedisSettings.from_dsn(_settings.redis_url)
                    )
                    await arq_pool.enqueue_job("post_draft_recap", draft_id)
                    await arq_pool.aclose()
                except Exception as exc:
                    logger.warning("draft.recap_enqueue.failed", draft_id=draft_id, error=str(exc))
            else:
                try:
                    import arq
                    from app.core.config import settings as _settings
                    redis_pool = await arq.create_pool(
                        arq.connections.RedisSettings.from_dsn(_settings.redis_url)
                    )
                    await arm_auto_draft_timer(redis_pool, draft_id, next_pick_num, deadline)
                    await redis_pool.aclose()
                except Exception as exc:
                    logger.warning("draft.arm_timer.failed", draft_id=draft_id, error=str(exc))

            logger.info("draft.pick.confirmed", draft_id=draft_id, pick_num=pick_num, player_id=player_id)
            return {"ok": True, "event_id": event_id}

        finally:
            await redis.delete(lock_key)

    async def on_pause(self, sid: str, data: dict) -> dict:
        """Commissioner-only: pause the draft clock.

        T-4-04: Role verified on every call, not cached.
        """
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]

        if not await self._is_commissioner(user_id, draft_id):
            return {"ok": False, "error": "not_commissioner"}

        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.set(CacheKey.draft_state(draft_id), "paused")

        event_id = await record_draft_event(redis, draft_id, "draft_paused", {"paused_by": user_id})
        await self.emit("draft_paused", {"event_id": event_id}, room=f"draft:{draft_id}")
        logger.info("draft.paused", draft_id=draft_id, user_id=user_id)
        return {"ok": True}

    async def on_resume(self, sid: str, data: dict) -> dict:
        """Commissioner-only: resume the draft with a 5-second countdown.

        T-4-04: Role verified on every call.
        """
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]

        if not await self._is_commissioner(user_id, draft_id):
            return {"ok": False, "error": "not_commissioner"}

        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.set(CacheKey.draft_state(draft_id), "live")

        event_id = await record_draft_event(redis, draft_id, "draft_resuming", {"countdown": "5"})
        await self.emit("draft_resuming", {"countdown": 5, "event_id": event_id}, room=f"draft:{draft_id}")
        logger.info("draft.resuming", draft_id=draft_id, user_id=user_id)
        return {"ok": True}

    async def on_end_draft(self, sid: str, data: dict) -> dict:
        """Commissioner-only: end the draft early."""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]

        if not await self._is_commissioner(user_id, draft_id):
            return {"ok": False, "error": "not_commissioner"}

        async with SessionLocal() as db:
            async with db.begin():
                draft_result = await db.execute(select(Draft).where(Draft.id == UUID(draft_id)))
                draft = draft_result.scalar_one_or_none()
                if draft:
                    draft.status = "complete"

        from app.core.redis import get_redis
        redis = await get_redis()
        event_id = await record_draft_event(redis, draft_id, "draft_complete", {"ended_by": user_id})
        await self.emit("draft_complete", {"event_id": event_id}, room=f"draft:{draft_id}")
        return {"ok": True}

    async def on_chat(self, sid: str, data: dict) -> dict:
        """DR-10: Broadcast chat message to all participants."""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        message = str(data.get("message", "")).strip()[:500]  # max 500 chars

        if not message:
            return {"ok": False, "error": "empty_message"}

        async with SessionLocal() as db:
            async with db.begin_nested():
                chat_msg = DraftChatMessage(
                    draft_id=UUID(draft_id),
                    user_id=UUID(user_id),
                    message=message,
                )
                db.add(chat_msg)
                await db.flush()
            await db.commit()

        from app.core.redis import get_redis
        redis = await get_redis()
        event_id = await record_draft_event(redis, draft_id, "chat_message", {
            "user_id": user_id,
            "message": message,
        })

        await self.emit("chat_message", {
            "user_id": user_id,
            "message": message,
            "created_at": str(time.time()),
            "event_id": event_id,
        }, room=f"draft:{draft_id}")
        return {"ok": True}

    async def on_react(self, sid: str, data: dict) -> dict:
        """DR-11: Add emoji reaction to a pick cell."""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        pick_num = int(data.get("pick_num", 0))
        emoji = str(data.get("emoji", ""))
        valid_emojis = {"fire", "laugh", "skeptical", "applause"}
        if emoji not in valid_emojis or pick_num <= 0:
            return {"ok": False, "error": "invalid_reaction"}

        reactions: dict = {}
        async with SessionLocal() as db:
            async with db.begin_nested():
                pick_result = await db.execute(
                    select(DraftPick).where(
                        DraftPick.draft_id == UUID(draft_id),
                        DraftPick.pick_num == pick_num,
                    )
                )
                pick = pick_result.scalar_one_or_none()
                if not pick:
                    return {"ok": False, "error": "pick_not_found"}
                reactions = dict(pick.reactions or {})
                reactors = reactions.get(emoji, [])
                if user_id not in reactors:
                    reactors.append(user_id)
                reactions[emoji] = reactors
                pick.reactions = reactions
                await db.flush()
            await db.commit()

        await self.emit("reaction_added", {
            "pick_num": pick_num,
            "reactions": reactions,
        }, room=f"draft:{draft_id}")
        return {"ok": True}

    async def on_reconnect(self, sid: str, data: dict) -> None:
        """DR-15: Replay missed events since last_event_id to reconnecting client.

        Uses exclusive XRANGE lower bound via replay_since().
        """
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        last_event_id = str(data.get("last_event_id", "-"))

        from app.core.redis import get_redis
        redis = await get_redis()
        events = await replay_since(redis, draft_id, last_event_id)

        for event_id, fields in events:
            await self.emit("replay_event", {"id": event_id, **fields}, to=sid)

        # Also send current deadline so client recalculates remaining time (D-07)
        deadline_str = await redis.get(CacheKey.draft_deadline(draft_id))
        if deadline_str:
            deadline_val = float(deadline_str)
            await self.emit("pick_deadline_sync", {"deadline": deadline_val}, to=sid)

        logger.info("draft.reconnect.replayed", draft_id=draft_id, events=len(events))

    async def on_queue_add(self, sid: str, data: dict) -> dict:
        """DR-04/D-09: Add player to personal queue."""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        player_id = str(data.get("player_id", ""))
        if not player_id:
            return {"ok": False, "error": "missing_player_id"}

        async with SessionLocal() as db:
            # Get current max position for ordering
            existing = await db.execute(
                select(DraftQueue).where(
                    DraftQueue.draft_id == UUID(draft_id),
                    DraftQueue.user_id == UUID(user_id),
                )
            )
            rows = existing.scalars().all()
            max_pos = max((r.position for r in rows), default=0)
            async with db.begin_nested():
                queue_item = DraftQueue(
                    draft_id=UUID(draft_id),
                    user_id=UUID(user_id),
                    player_id=player_id,
                    position=max_pos + 1,
                )
                db.add(queue_item)
                await db.flush()
            await db.commit()
        return {"ok": True, "position": max_pos + 1}

    async def on_queue_remove(self, sid: str, data: dict) -> dict:
        """D-09: Remove player from personal queue."""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        player_id = str(data.get("player_id", ""))

        async with SessionLocal() as db:
            async with db.begin():
                result = await db.execute(
                    select(DraftQueue).where(
                        DraftQueue.draft_id == UUID(draft_id),
                        DraftQueue.user_id == UUID(user_id),
                        DraftQueue.player_id == player_id,
                    )
                )
                row = result.scalar_one_or_none()
                if row:
                    await db.delete(row)
        return {"ok": True}

    async def on_queue_reorder(self, sid: str, data: dict) -> dict:
        """D-09: Reorder queue items. data={'order': ['player_id_1', 'player_id_2', ...]}"""
        session = await self.get_session(sid)
        draft_id = session["draft_id"]
        user_id = session["user_id"]
        new_order: list[str] = data.get("order", [])

        async with SessionLocal() as db:
            async with db.begin():
                result = await db.execute(
                    select(DraftQueue).where(
                        DraftQueue.draft_id == UUID(draft_id),
                        DraftQueue.user_id == UUID(user_id),
                    )
                )
                items = {row.player_id: row for row in result.scalars()}
                for i, player_id in enumerate(new_order, start=1):
                    if player_id in items:
                        items[player_id].position = i
        return {"ok": True}

    async def _is_commissioner(self, user_id: str, draft_id: str) -> bool:
        """T-4-04: Verify commissioner role server-side on every privileged call."""
        async with SessionLocal() as db:
            draft_result = await db.execute(select(Draft).where(Draft.id == UUID(draft_id)))
            draft = draft_result.scalar_one_or_none()
            if not draft:
                return False
            return str(draft.commissioner_user_id) == user_id
