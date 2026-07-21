import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — registers all models with Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


APP_SCHEMA = "app"


def do_run_migrations(connection):
    # version_table_schema puts alembic_version in our owned schema too
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=APP_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Use 'app' schema owned by doadmin to avoid public schema permission issues
    # on DO Managed PostgreSQL (PG15+ revoked public CREATE from non-owners).
    engine = create_async_engine(
        settings.database_url,
        connect_args={"server_settings": {"search_path": APP_SCHEMA}},
    )
    async with engine.connect() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {APP_SCHEMA}"))
        await conn.commit()
        print(f"INFO: running migrations in schema '{APP_SCHEMA}'", flush=True)
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
