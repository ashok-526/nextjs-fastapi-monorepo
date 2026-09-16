from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import and_, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.post import Post
from app.models.reaction import Reaction, ReactionType
from app.models.comment import Comment
from app.schemas.content import (
    CommentCreate,
    CommentOut,
    PostCreate,
    PostOut,
    ReactionCreate,
    ReactionOut,
)
from app.models.user import User
from app.services.notifications import get_redis
from app.services.social import is_blocked_either_way
import hashlib
import json
from pydantic import BaseModel, Field
from datetime import datetime, timezone


router = APIRouter(tags=["posts"])


def _profanity_guard(_: str) -> None:
    # Placeholder hook; implement real guard later
    return None


async def _get_post_or_404(db: AsyncSession, post_id: uuid.UUID) -> Post:
    res = await db.execute(select(Post).where(Post.id == post_id))
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostOut:
    _profanity_guard(payload.body)
    post = Post(
        author_id=current_user.id,
        body=payload.body,
        media_json=payload.media_json,
        visibility=payload.visibility,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return PostOut.model_validate(post)


@router.get("/posts/{post_id}")
async def get_post(post_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    cache_key = f"cache:post:{post_id}"
    r = await get_redis()
    cached = await r.get(cache_key)
    if cached:
        try:
            payload = json.loads(cached)
            etag = payload.get("etag")
            data = payload.get("data")
            inm = request.headers.get("if-none-match") or request.headers.get("If-None-Match")
            if etag and inm == etag:
                return Response(status_code=304)
            return JSONResponse(content=data, headers={"ETag": etag or "", "Cache-Control": "private, max-age=30"})
        except Exception:
            pass

    post = await _get_post_or_404(db, post_id)
    obj = PostOut.model_validate(post).model_dump()
    body_str = json.dumps(obj, default=str, separators=(",", ":"))
    etag = hashlib.sha256(body_str.encode("utf-8")).hexdigest()
    await r.setex(cache_key, 30, json.dumps({"etag": etag, "data": obj}, default=str))

    inm = request.headers.get("if-none-match") or request.headers.get("If-None-Match")
    if inm == etag:
        return Response(status_code=304)
    return JSONResponse(content=obj, headers={"ETag": etag, "Cache-Control": "private, max-age=30"})


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await _get_post_or_404(db, post_id)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    await db.execute(delete(Post).where(Post.id == post_id))
    await db.commit()
    return {"ok": True}


@router.post("/posts/{post_id}/react", response_model=ReactionOut)
async def react_to_post(
    post_id: uuid.UUID,
    payload: ReactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReactionOut:
    await _get_post_or_404(db, post_id)
    # Upsert: update if exists else create
    res = await db.execute(
        select(Reaction).where(Reaction.post_id == post_id, Reaction.user_id == current_user.id)
    )
    reaction = res.scalar_one_or_none()
    if reaction is None:
        reaction = Reaction(post_id=post_id, user_id=current_user.id, type=payload.type)
        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)
    else:
        await db.execute(
            update(Reaction)
            .where(Reaction.id == reaction.id)
            .values(type=payload.type)
        )
        await db.commit()
        await db.refresh(reaction)

    return ReactionOut.model_validate(reaction)


@router.delete("/posts/{post_id}/react")
async def remove_reaction(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_post_or_404(db, post_id)
    await db.execute(
        delete(Reaction).where(Reaction.post_id == post_id, Reaction.user_id == current_user.id)
    )
    await db.commit()
    return {"ok": True}


@router.get("/posts/{post_id}/reactions")
async def list_reactions(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(lambda: None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    post = await _get_post_or_404(db, post_id)
    if current_user is not None and await is_blocked_either_way(db, current_user.id, post.author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    q = (
        select(Reaction)
        .where(Reaction.post_id == post_id)
        .order_by(Reaction.user_id)
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    items = res.scalars().all()
    return {
        "data": [ReactionOut.model_validate(r).model_dump() for r in items],
        "limit": limit,
        "offset": offset,
        "count": len(items),
    }


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: uuid.UUID,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    await _get_post_or_404(db, post_id)
    _profanity_guard(payload.body)

    if payload.parent_comment_id is not None:
        # Ensure parent belongs to same post
        parent = (
            await db.execute(
                select(Comment).where(
                    Comment.id == payload.parent_comment_id, Comment.post_id == post_id
                )
            )
        ).scalar_one_or_none()
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent")

    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        parent_comment_id=payload.parent_comment_id,
        body=payload.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


@router.get("/posts/{post_id}/comments")
async def list_comments(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(lambda: None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    post = await _get_post_or_404(db, post_id)
    if current_user is not None and await is_blocked_either_way(db, current_user.id, post.author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Top-level comments
    top_q = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_comment_id.is_(None))
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(top_q)
    top_level = res.scalars().all()

    # Children (depth=1) for fetched top-level
    if top_level:
        parent_ids = [c.id for c in top_level]
        child_q = (
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_comment_id.in_(parent_ids))
            .order_by(Comment.created_at.asc())
        )
        child_res = await db.execute(child_q)
        children = child_res.scalars().all()
    else:
        children = []

    # Flatten order: parent then its children
    children_by_parent: Dict[uuid.UUID, List[Comment]] = {}
    for ch in children:
        children_by_parent.setdefault(ch.parent_comment_id, []).append(ch)  # type: ignore[arg-type]

    data: List[dict] = []
    for parent in top_level:
        data.append(CommentOut.model_validate(parent).model_copy(update={"depth": 0}).model_dump())
        for ch in children_by_parent.get(parent.id, []):
            data.append(CommentOut.model_validate(ch).model_copy(update={"depth": 1}).model_dump())

    return {"data": data, "limit": limit, "offset": offset, "count": len(data)}


class ReportBody(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


@router.post("/posts/{post_id}/report")
async def report_post(
    post_id: uuid.UUID,
    payload: ReportBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await _get_post_or_404(db, post_id)
    if await is_blocked_either_way(db, current_user.id, post.author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    r = await get_redis()
    event = {
        "id": str(uuid.uuid4()),
        "post_id": str(post_id),
        "reporter_id": str(current_user.id),
        "reason": payload.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await r.lpush("reports", json.dumps(event))
    await r.ltrim("reports", 0, 9999)
    return {"ok": True}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = res.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    await db.execute(delete(Comment).where(Comment.id == comment_id))
    await db.commit()
    return {"ok": True}
