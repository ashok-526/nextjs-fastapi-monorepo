from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.friendship import Friendship, FriendshipStatus
from app.models.block import Block


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    res = await db.execute(select(User).where(User.username == username))
    return res.scalar_one_or_none()


async def is_blocked_either_way(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    q = select(Block).where(
        or_(and_(Block.blocker_id == a, Block.blocked_id == b), and_(Block.blocker_id == b, Block.blocked_id == a))
    )
    res = await db.execute(q)
    return res.first() is not None


async def send_friend_request(db: AsyncSession, requester_id: uuid.UUID, addressee: User) -> Friendship:
    if requester_id == addressee.id:
        raise ValueError("Cannot friend yourself")

    if await is_blocked_either_way(db, requester_id, addressee.id):
        raise PermissionError("Blocked")

    # If reverse pending exists, accept it
    rev_q = select(Friendship).where(
        Friendship.requester_id == addressee.id,
        Friendship.addressee_id == requester_id,
        Friendship.status == FriendshipStatus.pending,
    )
    rev = (await db.execute(rev_q)).scalar_one_or_none()
    if rev is not None:
        await db.execute(
            update(Friendship)
            .where(Friendship.id == rev.id)
            .values(status=FriendshipStatus.accepted)
        )
        await db.commit()
        await db.refresh(rev)
        return rev

    # Prevent duplicates (pending or accepted) in same direction
    exists_q = select(Friendship).where(
        Friendship.requester_id == requester_id,
        Friendship.addressee_id == addressee.id,
        Friendship.status.in_([FriendshipStatus.pending, FriendshipStatus.accepted]),
    )
    exists = (await db.execute(exists_q)).scalar_one_or_none()
    if exists is not None:
        return exists

    fr = Friendship(requester_id=requester_id, addressee_id=addressee.id, status=FriendshipStatus.pending)
    db.add(fr)
    await db.commit()
    await db.refresh(fr)
    return fr


async def accept_friend_request(db: AsyncSession, addressee_id: uuid.UUID, request_id: uuid.UUID) -> Friendship:
    q = select(Friendship).where(
        Friendship.id == request_id,
        Friendship.addressee_id == addressee_id,
        Friendship.status == FriendshipStatus.pending,
    )
    fr = (await db.execute(q)).scalar_one_or_none()
    if fr is None:
        raise LookupError("Request not found")

    if await is_blocked_either_way(db, fr.requester_id, fr.addressee_id):
        raise PermissionError("Blocked")

    await db.execute(
        update(Friendship)
        .where(Friendship.id == fr.id)
        .values(status=FriendshipStatus.accepted)
    )
    await db.commit()
    await db.refresh(fr)
    return fr


async def decline_friend_request(db: AsyncSession, addressee_id: uuid.UUID, request_id: uuid.UUID) -> None:
    q = select(Friendship.id).where(
        Friendship.id == request_id,
        Friendship.addressee_id == addressee_id,
        Friendship.status == FriendshipStatus.pending,
    )
    fr = (await db.execute(q)).scalar_one_or_none()
    if fr is None:
        raise LookupError("Request not found")
    await db.execute(delete(Friendship).where(Friendship.id == request_id))
    await db.commit()


async def list_friends(db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int) -> Sequence[User]:
    # Union of both directions
    left = (
        select(User)
        .join(Friendship, Friendship.addressee_id == User.id)
        .where(Friendship.requester_id == user_id, Friendship.status == FriendshipStatus.accepted)
    )
    right = (
        select(User)
        .join(Friendship, Friendship.requester_id == User.id)
        .where(Friendship.addressee_id == user_id, Friendship.status == FriendshipStatus.accepted)
    )
    union_q = left.union_all(right).limit(limit).offset(offset)
    res = await db.execute(union_q)
    return res.scalars().all()


async def block_user(db: AsyncSession, blocker_id: uuid.UUID, blocked: User) -> Block:
    if blocker_id == blocked.id:
        raise ValueError("Cannot block yourself")
    # Idempotent: ignore if exists
    existing = await db.execute(
        select(Block).where(Block.blocker_id == blocker_id, Block.blocked_id == blocked.id)
    )
    blk = existing.scalar_one_or_none()
    if blk is not None:
        return blk
    blk = Block(blocker_id=blocker_id, blocked_id=blocked.id)
    db.add(blk)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Another process created it; fetch
        blk = (
            await db.execute(
                select(Block).where(Block.blocker_id == blocker_id, Block.blocked_id == blocked.id)
            )
        ).scalar_one()
    await db.refresh(blk)
    return blk


async def unblock_user(db: AsyncSession, blocker_id: uuid.UUID, blocked: User) -> None:
    await db.execute(delete(Block).where(Block.blocker_id == blocker_id, Block.blocked_id == blocked.id))
    await db.commit()

