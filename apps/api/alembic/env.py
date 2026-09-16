from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
import os
import sys
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _make_async_url(url: str) -> str:
    if url.startswith("postgresql+") and "+asyncpg" not in url:
        return url.replace("postgresql+psycopg", "postgresql+asyncpg").replace(
            "postgresql+psycopg2", "postgresql+asyncpg"
        ).replace("postgresql://", "postgresql+asyncpg://")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


settings = get_settings()
ASYNC_DATABASE_URL = _make_async_url(settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(ASYNC_DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
