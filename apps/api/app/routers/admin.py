from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_current_user
from app.models.user import User
from app.services.notifications import get_redis


router = APIRouter(prefix="/admin", tags=["admin"])


def _is_admin(u: User) -> bool:
    env = os.getenv("ADMIN_USERS", "admin")
    allowed = {x.strip() for x in env.split(",") if x.strip()}
    return (u.username in allowed) or (u.email in allowed)


@router.get("/reports")
async def list_reports(
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    r = await get_redis()
    # Redis lists are 0-based inclusive ranges
    end = offset + limit - 1
    raw_items = await r.lrange("reports", offset, end)
    items = []
    for raw in raw_items or []:
        try:
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            items.append(json.loads(text))
        except Exception:
            continue
    return {"data": items, "limit": limit, "offset": offset, "count": len(items)}

