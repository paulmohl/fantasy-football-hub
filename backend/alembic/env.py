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
        # PG15+: public schema is owned by pg_database_owner, not the login user.
        # doadmin can't GRANT on a schema it doesn't own, so skip the GRANT.
        # Instead, run migrations AS pg_database_owner — SET ROLE (without LOCAL)
        # persists beyond commit for the session, so alembic's transaction inherits it.
        try:
            await conn.execute(text("SET ROLE pg_database_owner"))
            await conn.commit()
            print("INFO: running migrations as pg_database_owner", flush=True)
        except Exception as e:
            print(f"WARNING: SET ROLE pg_database_owner failed ({e}); migrations may fail", flush=True)
            try:
                await conn.rollback()
            except Exception:
                pass
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
