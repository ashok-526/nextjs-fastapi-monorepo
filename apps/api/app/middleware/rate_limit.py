from __future__ import annotations

import time
import uuid
from typing import Callable

from authlib.jose import jwt, JoseError
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.services.notifications import get_redis


WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only HTTP requests
        if request.scope.get("type") != "http":
            return await call_next(request)

        method = request.method.upper()
        path = request.url.path

        # Skip health and preflight
        if method == "OPTIONS" or path == "/health":
            return await call_next(request)

        # Determine bucket and limits
        bucket_key, limit = await self._classify(request)

        if bucket_key and limit:
            allowed, remaining = await self._check_rate(bucket_key, limit, WINDOW_SECONDS)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests"},
                    headers={
                        "Retry-After": str(WINDOW_SECONDS),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(max(0, remaining)),
                    },
                )

        return await call_next(request)

    async def _classify(self, request: Request) -> tuple[str | None, int | None]:
        method = request.method.upper()
        path = request.url.path
        client_ip = (request.headers.get("x-forwarded-for") or request.client.host or "unknown").split(",")[0].strip()

        # Auth routes: per-IP 5/min
        if path.startswith("/auth/"):
            return f"rl:ip:auth:{client_ip}", 5

        # Determine subject (user id) from JWT if present
        subject: str | None = None
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            try:
                claims = jwt.decode(token, get_settings().JWT_SECRET)
                claims.validate()
                sub = claims.get("sub")
                subject = str(uuid.UUID(str(sub)))
            except (JoseError, Exception):  # noqa: BLE001
                subject = None

        # Mutations: per-user 30/min (fallback IP if not authed)
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            ident = subject or f"ip:{client_ip}"
            return f"rl:user:mut:{ident}", 30

        # Reads (GET): per-user 120/min (fallback IP)
        if method == "GET":
            ident = subject or f"ip:{client_ip}"
            return f"rl:user:read:{ident}", 120

        return None, None

    async def _check_rate(self, key: str, limit: int, window_s: int) -> tuple[bool, int]:
        now_ms = int(time.time() * 1000)
        oldest = now_ms - window_s * 1000
        member = f"{now_ms}-{uuid.uuid4()}"

        r = await get_redis()
        pipe = r.pipeline()
        pipe.zadd(key, {member: now_ms})
        pipe.zremrangebyscore(key, 0, oldest)
        pipe.zcard(key)
        pipe.expire(key, window_s)
        _, _, count, _ = await pipe.execute()

        remaining = max(0, limit - int(count))
        return (count <= limit), remaining

