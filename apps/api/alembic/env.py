# alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.shared.db.base import Base
from app.shared.db.session import _get_migrations_database_url
import app.modules.tenants.models  # noqa: F401 — registers Tenant with metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_get_migrations_database_url(sync=True),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(
        _get_migrations_database_url(sync=False),
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
