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


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        # Diagnostic: log current user and what DDL they can do
        try:
            r = await conn.execute(text(
                "SELECT current_user, session_user, "
                "has_database_privilege(current_database(), 'CREATE') AS db_create, "
                "has_schema_privilege('public', 'CREATE') AS pub_create"
            ))
            row = r.first()
            print(
                f"INFO: current_user={row[0]} session_user={row[1]} "
                f"db_create={row[2]} public_schema_create={row[3]}",
                flush=True,
            )
            await conn.rollback()
        except Exception as e:
            print(f"INFO: privilege check failed: {e}", flush=True)
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
