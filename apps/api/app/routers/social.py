from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.services.social import (
    accept_friend_request,
    block_user,
    decline_friend_request,
    get_user_by_username,
    is_blocked_either_way,
    list_friends,
    send_friend_request,
    unblock_user,
)


router = APIRouter(prefix="/social", tags=["social"])


@router.post("/friend-requests/{username}")
async def post_friend_request(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await get_user_by_username(db, username)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        fr = await send_friend_request(db, current_user.id, target)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blocked")

    return {"id": str(fr.id), "status": fr.status.value}


@router.post("/friend-requests/{request_id}/accept")
async def accept_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        fr = await accept_friend_request(db, current_user.id, request_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blocked")
    return {"id": str(fr.id), "status": fr.status.value}


@router.post("/friend-requests/{request_id}/decline")
async def decline_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await decline_friend_request(db, current_user.id, request_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {"ok": True}


@router.get("/friends")
async def get_friends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    users = await list_friends(db, current_user.id, limit=limit, offset=offset)
    # Exclude blocked either way
    filtered = []
    for u in users:
        if not await is_blocked_either_way(db, current_user.id, u.id):
            filtered.append(u)
    return {
        "data": [
            {"id": str(u.id), "username": u.username}
            for u in filtered
        ],
        "limit": limit,
        "offset": offset,
        "count": len(filtered),
    }


@router.post("/block/{username}")
async def block(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await get_user_by_username(db, username)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        blk = await block_user(db, current_user.id, target)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"blocker_id": str(blk.blocker_id), "blocked_id": str(blk.blocked_id)}


@router.delete("/block/{username}")
async def unblock(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = await get_user_by_username(db, username)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await unblock_user(db, current_user.id, target)
    return {"ok": True}
