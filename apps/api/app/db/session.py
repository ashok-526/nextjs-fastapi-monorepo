from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def _make_async_url(url: str) -> str:
    # Convert a sync URL to asyncpg if needed
    if url.startswith("postgresql+") and "+asyncpg" not in url:
        return url.replace("postgresql+psycopg", "postgresql+asyncpg").replace(
            "postgresql+psycopg2", "postgresql+asyncpg"
        ).replace("postgresql://", "postgresql+asyncpg://")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


settings = get_settings()
ASYNC_DATABASE_URL = _make_async_url(settings.DATABASE_URL)

engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

