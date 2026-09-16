from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import and_, exists, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.friendship import Friendship, FriendshipStatus
from app.models.block import Block
from app.models.profile import Visibility
from app.services.pagination import decode_keyset, encode_keyset


async def fetch_feed(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 25,
    cursor: str | None = None,
) -> tuple[Sequence[Post], str | None]:
    limit = max(1, min(limit, 25))

    # Friends subquery (both directions)
    left = select(Friendship.addressee_id.label("friend_id")).where(
        Friendship.requester_id == user_id,
        Friendship.status == FriendshipStatus.accepted,
    )
    right = select(Friendship.requester_id.label("friend_id")).where(
        Friendship.addressee_id == user_id,
        Friendship.status == FriendshipStatus.accepted,
    )
    friends_sq = left.union_all(right).subquery()

    # Visibility rules: self -> any; friend -> public or friends
    visible_clause = or_(
        Post.author_id == user_id,
        and_(
            Post.author_id.in_(select(friends_sq.c.friend_id)),
            Post.visibility.in_([Visibility.public, Visibility.friends]),
        ),
    )

    # Exclude blocks either way
    block_exists = (
        exists()
        .where(
            or_(
                and_(Block.blocker_id == user_id, Block.blocked_id == Post.author_id),
                and_(Block.blocker_id == Post.author_id, Block.blocked_id == user_id),
            )
        )
        .correlate(Post.__table__)
    )

    q = (
        select(Post)
        .where(visible_clause, not_(block_exists))
        .order_by(Post.created_at.desc(), Post.id.desc())
        .limit(limit)
    )

    if cursor:
        created_at_cur, id_cur = decode_keyset(cursor)
        q = q.where(
            or_(
                Post.created_at < created_at_cur,
                and_(Post.created_at == created_at_cur, Post.id < id_cur),
            )
        )

    res = await db.execute(q)
    items = res.scalars().all()

    next_cursor: str | None = None
    if len(items) == limit:
        last = items[-1]
        next_cursor = encode_keyset(last.created_at, last.id)  # type: ignore[arg-type]

    return items, next_cursor

