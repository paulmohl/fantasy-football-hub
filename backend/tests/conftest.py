"""Pytest fixtures for Phase 1 tests.

Provides:
  - async_client: AsyncClient pointing at the FastAPI test app
  - test_db: AsyncSession connected to an in-memory SQLite database
  - mock_redis: MagicMock for redis (avoids needing real Redis in unit tests)
"""
import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app

# Use in-memory SQLite for tests (async via aiosqlite)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _patch_jsonb_for_sqlite(metadata) -> None:
    """Replace PostgreSQL JSONB with JSON so SQLite in-memory tests can create tables."""
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB
    for table in metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    _patch_jsonb_for_sqlite(Base.metadata)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session


@pytest.fixture
def mock_redis():
    """Return a MagicMock that acts like an async Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.xadd = AsyncMock(return_value=b"1714000000000-0")
    redis.xrange = AsyncMock(return_value=[])
    redis.xlen = AsyncMock(return_value=0)
    redis.sadd = AsyncMock(return_value=1)
    redis.srem = AsyncMock(return_value=1)
    redis.sismember = AsyncMock(return_value=True)
    redis.smembers = AsyncMock(return_value=set())
    redis.scard = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def mock_redis_streams():
    """Redis mock with realistic xadd/xrange return values for stream tests."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.xadd = AsyncMock(return_value=b"1714000000001-0")
    redis.xrange = AsyncMock(return_value=[
        (b"1714000000001-0", {b"type": b"pick_confirmed", b"player_id": b"6783", b"pick_num": b"1"}),
    ])
    redis.xlen = AsyncMock(return_value=1)
    redis.sadd = AsyncMock(return_value=1)
    redis.srem = AsyncMock(return_value=1)
    redis.sismember = AsyncMock(return_value=True)
    redis.smembers = AsyncMock(return_value={b"6783", b"4046", b"1234"})
    redis.scard = AsyncMock(return_value=3)
    return redis


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with DB and Redis overridden to in-memory fixtures."""
    async def override_get_db():
        yield test_db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
