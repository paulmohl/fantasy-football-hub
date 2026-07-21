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
        # PG15+ revoked default CREATE on public schema.
        # SET ROLE pg_database_owner grants us schema ownership for the session
        # so we can GRANT it back to the app user permanently.
        try:
            await conn.execute(text("SET ROLE pg_database_owner"))
            # SESSION_USER stays as the login user (doadmin) even after SET ROLE;
            # CURRENT_USER would be pg_database_owner here — wrong target
            await conn.execute(text("GRANT ALL ON SCHEMA public TO SESSION_USER"))
            await conn.execute(text("RESET ROLE"))
            await conn.commit()
        except Exception as e:
            print(f"WARNING: public schema grant failed ({e}), proceeding anyway", flush=True)
            await conn.rollback()
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
