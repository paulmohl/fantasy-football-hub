import difflib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.player import PlayerCrossMap

FUZZY_THRESHOLD = 0.85


class PlayerIDMapper:
    """Resolve platform player IDs to canonical Sleeper IDs.

    Primary: direct lookup in player_cross_map table.
    Fallback: fuzzy match by (full_name, position) using SequenceMatcher.
    Logs unmapped IDs for monitoring.
    """

    async def yahoo_to_sleeper(
        self,
        db: AsyncSession,
        yahoo_id: str,
        full_name: str | None = None,
        position: str | None = None,
        team: str | None = None,
    ) -> str | None:
        result = await db.execute(
            select(PlayerCrossMap).where(PlayerCrossMap.yahoo_id == yahoo_id)
        )
        row = result.scalar_one_or_none()
        if row:
            return row.sleeper_id
        if full_name:
            return await self._fuzzy_lookup(db, full_name, position, team)
        logger.warning("player.yahoo_id.unmapped", yahoo_id=yahoo_id)
        return None

    async def espn_to_sleeper(
        self,
        db: AsyncSession,
        espn_id: str,
        full_name: str | None = None,
        position: str | None = None,
        team: str | None = None,
    ) -> str | None:
        result = await db.execute(
            select(PlayerCrossMap).where(PlayerCrossMap.espn_id == espn_id)
        )
        row = result.scalar_one_or_none()
        if row:
            return row.sleeper_id
        if full_name:
            return await self._fuzzy_lookup(db, full_name, position, team)
        logger.warning("player.espn_id.unmapped", espn_id=espn_id)
        return None

    async def _fuzzy_lookup(
        self,
        db: AsyncSession,
        full_name: str,
        position: str | None,
        team: str | None,
    ) -> str | None:
        """Fuzzy match by full_name + optional position/team filters."""
        candidates_q = select(PlayerCrossMap)
        if position:
            candidates_q = candidates_q.where(PlayerCrossMap.position == position)
        result = await db.execute(candidates_q)
        candidates = result.scalars().all()

        best_ratio = 0.0
        best_match: PlayerCrossMap | None = None
        for candidate in candidates:
            ratio = difflib.SequenceMatcher(
                None, full_name.lower(), candidate.full_name.lower()
            ).ratio()
            if ratio > FUZZY_THRESHOLD and ratio > best_ratio:
                if team and candidate.team and candidate.team != team:
                    continue
                best_ratio = ratio
                best_match = candidate

        if best_match:
            logger.info(
                "player.fuzzy.matched",
                full_name=full_name,
                matched=best_match.full_name,
                ratio=best_ratio,
            )
            return best_match.sleeper_id

        logger.warning("player.fuzzy.unmapped", full_name=full_name, position=position)
        return None
