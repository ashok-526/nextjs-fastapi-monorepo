from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.notification import Notification


_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        url = get_settings().REDIS_URL
        _redis_client = redis.from_url(url, decode_responses=False)  # bytes payloads
    return _redis_client


def _json_default(obj: Any):  # noqa: ANN401
    if isinstance(obj, (uuid.UUID,)):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def _publish(user_id: uuid.UUID, event: Dict[str, Any]) -> None:
    client = await get_redis()
    channel = f"user:{user_id}:events"
    await client.publish(channel, json.dumps(event, default=_json_default))


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    type_: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Notification:
    notif = Notification(user_id=user_id, type=type_, payload=payload or {}, is_read=False)
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    await _publish(
        user_id,
        {
            "id": notif.id,
            "type": notif.type,
            "payload": notif.payload or {},
            "is_read": notif.is_read,
            "created_at": notif.created_at,
        },
    )
    return notif


# Convenience helpers for common events
async def notify_friend_request_sent(db: AsyncSession, to_user_id: uuid.UUID, requester_id: uuid.UUID) -> Notification:
    return await create_notification(
        db,
        user_id=to_user_id,
        type_="friend_request_sent",
        payload={"requester_id": str(requester_id)},
    )


async def notify_friend_request_accepted(
    db: AsyncSession, requester_id: uuid.UUID, addressee_id: uuid.UUID
) -> Notification:
    # requester is notified that addressee accepted
    return await create_notification(
        db,
        user_id=requester_id,
        type_="friend_request_accepted",
        payload={"user_id": str(addressee_id)},
    )


async def notify_post_commented(
    db: AsyncSession,
    post_author_id: uuid.UUID,
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    commenter_id: uuid.UUID,
) -> Notification:
    return await create_notification(
        db,
        user_id=post_author_id,
        type_="post_commented",
        payload={
            "post_id": str(post_id),
            "comment_id": str(comment_id),
            "commenter_id": str(commenter_id),
        },
    )


async def notify_post_reacted(
    db: AsyncSession,
    post_author_id: uuid.UUID,
    post_id: uuid.UUID,
    reactor_id: uuid.UUID,
    reaction_type: str,
) -> Notification:
    return await create_notification(
        db,
        user_id=post_author_id,
        type_="post_reacted",
        payload={
            "post_id": str(post_id),
            "reactor_id": str(reactor_id),
            "reaction_type": reaction_type,
        },
    )

