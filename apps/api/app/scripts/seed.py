from __future__ import annotations

import asyncio
import random
import string
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.user import User
from app.models.post import Post
from app.models.reaction import Reaction, ReactionType
from app.models.friendship import Friendship, FriendshipStatus
from app.core.security import hash_password


FIRST_NAMES = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy",
    "Karl", "Laura", "Mallory", "Niaj", "Olivia", "Peggy", "Quentin", "Rupert", "Sybil", "Trent",
]


def rand_username(n=8):
    return "user_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


async def create_users(db: AsyncSession, n: int) -> List[User]:
    users: List[User] = []
    for i in range(n):
        uname = rand_username()
        u = User(
            email=f"{uname}@example.com",
            username=uname,
            password_hash=hash_password("password123"),
        )
        db.add(u)
        users.append(u)
    await db.commit()
    for u in users:
        await db.refresh(u)
    return users


async def create_posts(db: AsyncSession, users: List[User], n: int) -> List[Post]:
    posts: List[Post] = []
    for _ in range(n):
        author = random.choice(users)
        p = Post(author_id=author.id, body=f"Post by {author.username}", media_json=None, visibility=random.choice(["public", "friends", "private"]))
        db.add(p)
        posts.append(p)
    await db.commit()
    for p in posts:
        await db.refresh(p)
    return posts


async def create_friendships(db: AsyncSession, users: List[User], probability: float = 0.1):
    for a in users:
        for b in users:
            if a.id == b.id:
                continue
            if random.random() < probability:
                # Ensure only one direction created
                exists = await db.execute(
                    select(Friendship).where(
                        ((Friendship.requester_id == a.id) & (Friendship.addressee_id == b.id))
                        | ((Friendship.requester_id == b.id) & (Friendship.addressee_id == a.id))
                    )
                )
                if exists.scalar_one_or_none() is None:
                    fr = Friendship(requester_id=a.id, addressee_id=b.id, status=FriendshipStatus.accepted)
                    db.add(fr)
    await db.commit()


async def create_reactions(db: AsyncSession, users: List[User], posts: List[Post], probability: float = 0.2):
    for p in posts:
        for u in random.sample(users, k=max(1, int(len(users) * probability))):
            r = Reaction(post_id=p.id, user_id=u.id, type=random.choice(list(ReactionType)))
            db.add(r)
    try:
        await db.commit()
    except Exception:
        await db.rollback()


async def main():
    async with SessionLocal() as db:
        users = await create_users(db, 50)
        await create_friendships(db, users, probability=0.1)
        posts = await create_posts(db, users, 200)
        await create_reactions(db, users, posts, probability=0.05)
    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(main())

