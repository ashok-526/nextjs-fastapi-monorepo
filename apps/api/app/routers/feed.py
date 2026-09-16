from __future__ import annotations

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.content import PostOut
from app.services.feed import fetch_feed


router = APIRouter(tags=["feed"])


@router.get("/feed")
async def get_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cursor: Optional[str] = Query(default=None),
):
    items, next_cursor = await fetch_feed(db, current_user.id, limit=25, cursor=cursor)
    return {
        "data": [PostOut.model_validate(p).model_dump() for p in items],
        "next_cursor": next_cursor,
    }

