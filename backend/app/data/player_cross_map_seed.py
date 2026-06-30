import csv
import io
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.player import PlayerCrossMap

FFB_IDS_URL = "https://raw.githubusercontent.com/mayscopeland/ffb_ids/main/player_ids.csv"
FALLBACK_URL = "https://github.com/dynastyprocess/data/raw/main/player_ids.csv"


def _parse_csv_rows(csv_text: str) -> list[dict]:
    """Parse CSV text into a list of row dicts, skipping rows without sleeper_id."""
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        sleeper_id = (row.get("sleeper_id") or "").strip()
        if not sleeper_id:
            continue
        rows.append({
            "sleeper_id": sleeper_id,
            "yahoo_id": (row.get("yahoo_id") or "").strip() or None,
            "espn_id": (row.get("espn_id") or "").strip() or None,
            "full_name": (row.get("name") or row.get("full_name") or "").strip(),
            "position": (row.get("position") or "").strip() or None,
            "team": (row.get("team") or "").strip() or None,
            "updated_at": datetime.now(UTC).replace(tzinfo=None),
        })
    return rows


async def _pg_upsert(db: AsyncSession, rows: list[dict]) -> None:
    """PostgreSQL bulk upsert via ON CONFLICT DO UPDATE."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    stmt = pg_insert(PlayerCrossMap).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sleeper_id"],
        set_={
            "yahoo_id": stmt.excluded.yahoo_id,
            "espn_id": stmt.excluded.espn_id,
            "full_name": stmt.excluded.full_name,
            "position": stmt.excluded.position,
            "team": stmt.excluded.team,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    await db.execute(stmt)


async def _generic_upsert(db: AsyncSession, rows: list[dict]) -> None:
    """Row-by-row upsert fallback (SQLite / testing)."""
    for row in rows:
        result = await db.execute(
            select(PlayerCrossMap).where(PlayerCrossMap.sleeper_id == row["sleeper_id"])
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            db.add(PlayerCrossMap(**row))
        else:
            for k, v in row.items():
                setattr(obj, k, v)
    await db.flush()


async def load_player_cross_map_from_csv(csv_text: str, db: AsyncSession) -> int:
    """Bulk upsert player cross-map rows from CSV text.

    CSV must have columns: sleeper_id, yahoo_id, espn_id, name, position
    Returns number of rows upserted.
    """
    rows = _parse_csv_rows(csv_text)
    if not rows:
        logger.warning("player_cross_map.seed.empty_csv")
        return 0

    conn = await db.connection()
    if conn.dialect.name == "postgresql":
        await _pg_upsert(db, rows)
    else:
        await _generic_upsert(db, rows)

    await db.flush()
    logger.info("player_cross_map.seed.complete", count=len(rows))
    return len(rows)
