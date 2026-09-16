from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from authlib.jose import jwt, JoseError

from app.core.config import get_settings
from app.services.notifications import get_redis


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(default=None)):
    await websocket.accept()
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.JWT_SECRET)
        claims.validate()
        sub = claims.get("sub")
        user_id = uuid.UUID(str(sub))
    except (JoseError, Exception):  # noqa: BLE001
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    channel = f"user:{user_id}:events"
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message is None:
                continue
            if message.get("type") != "message":
                continue
            data = message.get("data")
            try:
                text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
            except Exception:  # noqa: BLE001
                text = json.dumps({"error": "invalid_event"})
            await websocket.send_text(text)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
        finally:
            await pubsub.close()

