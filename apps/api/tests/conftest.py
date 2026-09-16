import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient


# Ensure import path includes app package
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> None:
    os.environ.setdefault("JWT_SECRET", "testsecret")
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/app_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("S3_ENDPOINT", "http://localhost:9000")
    os.environ.setdefault("S3_BUCKET", "media")
    os.environ.setdefault("S3_ACCESS_KEY", "minioadmin")
    os.environ.setdefault("S3_SECRET_KEY", "minioadmin")
    os.environ.setdefault("NEXT_PUBLIC_CDN_URL", "http://localhost:9000/media")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def app_setup() -> AsyncGenerator[None, None]:
    from app.db.base import Base
    from app.db.session import engine

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        # Drop tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


class _FakePipe:
    def __init__(self, store: dict):
        self.s = store
        self.ops = []

    def zadd(self, key, mapping):
        self.ops.append(("zadd", key, mapping))
        return self

    def zremrangebyscore(self, key, minscore, maxscore):
        self.ops.append(("zremrangebyscore", key, minscore, maxscore))
        return self

    def zcard(self, key):
        self.ops.append(("zcard", key))
        return self

    def expire(self, key, ttl):
        self.ops.append(("expire", key, ttl))
        return self

    async def execute(self):
        out = []
        for op in self.ops:
            name = op[0]
            if name == "zadd":
                _, key, mapping = op
                z = self.s.setdefault(key, [])
                for member, score in mapping.items():
                    z.append((score, member))
                out.append(1)
            elif name == "zremrangebyscore":
                _, key, minscore, maxscore = op
                z = self.s.get(key, [])
                self.s[key] = [(s, m) for (s, m) in z if not (minscore <= s <= maxscore)]
                out.append(1)
            elif name == "zcard":
                _, key = op
                out.append(len(self.s.get(key, [])))
            elif name == "expire":
                out.append(True)
        self.ops.clear()
        return out


class _FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        val = self.store.get(key)
        if val is None:
            return None
        if isinstance(val, (bytes, bytearray)):
            return val
        return str(val).encode("utf-8")

    async def setex(self, key, ttl, value):
        self.store[key] = value
        return True

    async def publish(self, channel, message):
        # no-op
        return 1

    def pipeline(self):
        return _FakePipe(self.store)


@pytest.fixture(autouse=True)
async def mock_redis(monkeypatch):
    from app.services import notifications as notif_mod

    client = _FakeRedis()

    async def _get():
        return client

    monkeypatch.setattr(notif_mod, "get_redis", _get)
    yield


@pytest.fixture()
async def client(app_setup) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

