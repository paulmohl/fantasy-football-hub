"""Tests for PlayerIDMapper and player_cross_map_seed (03-07)."""
from datetime import UTC, datetime

import pytest

from app.models.player import PlayerCrossMap
from app.services.player_id_mapper import PlayerIDMapper

SAMPLE_CSV = """\
sleeper_id,yahoo_id,espn_id,name,position,team
1001,4567,111,Josh Allen,QB,BUF
1002,9876,222,Davante Adams,WR,LV
1003,,333,Patrick Mahomes,QB,KC
"""

MISSING_SLEEPER_CSV = """\
sleeper_id,yahoo_id,espn_id,name,position,team
,4567,111,Josh Allen,QB,BUF
1002,9876,222,Davante Adams,WR,LV
"""


def _pcm(sleeper_id: str, yahoo_id: str | None = None, espn_id: str | None = None,
         full_name: str = "Player", position: str | None = None, team: str | None = None):
    return PlayerCrossMap(
        sleeper_id=sleeper_id,
        yahoo_id=yahoo_id,
        espn_id=espn_id,
        full_name=full_name,
        position=position,
        team=team,
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )


# ── Direct lookup tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_yahoo_to_sleeper_direct(test_db):
    test_db.add(_pcm("123", yahoo_id="456", full_name="Josh Allen", position="QB"))
    await test_db.flush()

    mapper = PlayerIDMapper()
    result = await mapper.yahoo_to_sleeper(test_db, "456")
    assert result == "123"


@pytest.mark.asyncio
async def test_espn_to_sleeper_direct(test_db):
    test_db.add(_pcm("123", espn_id="789", full_name="Davante Adams", position="WR"))
    await test_db.flush()

    mapper = PlayerIDMapper()
    result = await mapper.espn_to_sleeper(test_db, "789")
    assert result == "123"


@pytest.mark.asyncio
async def test_yahoo_to_sleeper_not_found(test_db):
    mapper = PlayerIDMapper()
    result = await mapper.yahoo_to_sleeper(test_db, "nonexistent")
    assert result is None


# ── Fuzzy fallback tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fuzzy_fallback_high_confidence(test_db):
    test_db.add(_pcm("500", full_name="Josh Allen", position="QB", team="BUF"))
    await test_db.flush()

    mapper = PlayerIDMapper()
    # No direct yahoo_id match, but name+position match
    result = await mapper.yahoo_to_sleeper(test_db, "unknown_id", full_name="Josh Allen", position="QB")
    assert result == "500"


@pytest.mark.asyncio
async def test_fuzzy_fallback_below_threshold(test_db):
    test_db.add(_pcm("600", full_name="Josh Allen", position="QB"))
    await test_db.flush()

    mapper = PlayerIDMapper()
    # "John Smith" vs "Josh Allen" — low similarity
    result = await mapper.yahoo_to_sleeper(test_db, "unknown_id", full_name="John Smith", position="QB")
    assert result is None


@pytest.mark.asyncio
async def test_fuzzy_false_positive_guard(test_db):
    """Team mismatch should prevent a match even when names are similar."""
    test_db.add(_pcm("700", full_name="Chris Williams", position="WR", team="CHI"))
    await test_db.flush()

    mapper = PlayerIDMapper()
    # "Chris Williams" vs "Chris Williams" — same name, same position, DIFFERENT team
    result = await mapper.yahoo_to_sleeper(
        test_db, "unknown_id", full_name="Chris Williams", position="WR", team="DAL"
    )
    assert result is None


# ── CSV seed tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_load_csv_bulk_upsert(test_db):
    from app.data.player_cross_map_seed import load_player_cross_map_from_csv

    count = await load_player_cross_map_from_csv(SAMPLE_CSV, test_db)
    assert count == 3

    mapper = PlayerIDMapper()
    assert await mapper.yahoo_to_sleeper(test_db, "4567") == "1001"
    assert await mapper.espn_to_sleeper(test_db, "222") == "1002"

    # Second call — same data should not create duplicates
    count2 = await load_player_cross_map_from_csv(SAMPLE_CSV, test_db)
    assert count2 == 3

    from sqlalchemy import func, select
    total = await test_db.execute(select(func.count()).select_from(PlayerCrossMap))
    assert total.scalar() == 3


@pytest.mark.asyncio
async def test_csv_missing_sleeper_id_skipped(test_db):
    from app.data.player_cross_map_seed import load_player_cross_map_from_csv

    count = await load_player_cross_map_from_csv(MISSING_SLEEPER_CSV, test_db)
    assert count == 1  # Only the row with sleeper_id="1002" is valid
