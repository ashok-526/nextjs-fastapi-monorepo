from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.app.db.session import get_session


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_session)) -> Token:
    # Check existing by email or username
    existing = await db.execute(
        select(User).where(or_(User.email == payload.email, User.username == payload.username))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_session)) -> Token:
    q = select(User).where(
        or_(User.email == payload.email_or_username, User.username == payload.email_or_username)
    )
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id)
    return Token(access_token=token)

