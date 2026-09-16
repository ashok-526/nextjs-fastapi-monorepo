from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app.core.config import get_settings
from app.db.session import get_session
from app.models.user import User
from app.models.profile import Profile, Visibility
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.profile import MeOut, ProfileOut, ProfileUpdate, PublicProfileOut


router = APIRouter(tags=["profile"])


async def _get_db() -> AsyncSession:
    async for s in get_session():
        return s


async def _get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    db: AsyncSession = Depends(_get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.JWT_SECRET)
        claims.validate()
    except JoseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = claims.get("sub")
    try:
        user_id = uuid.UUID(str(sub))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def _optional_viewer_id(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Optional[uuid.UUID]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.JWT_SECRET)
        claims.validate()
        sub = claims.get("sub")
        return uuid.UUID(str(sub))
    except Exception:  # noqa: BLE001
        return None


async def _get_or_create_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    res = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = res.scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user_id, visibility=Visibility.public)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def _are_friends(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    if a == b:
        return True
    q = select(Friendship.id).where(
        Friendship.status == FriendshipStatus.accepted,
        or_(
            (Friendship.requester_id == a) & (Friendship.addressee_id == b),
            (Friendship.requester_id == b) & (Friendship.addressee_id == a),
        ),
    )
    res = await db.execute(q)
    return res.first() is not None


@router.get("/me", response_model=MeOut)
async def get_me(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(_get_db),
) -> MeOut:
    profile = await _get_or_create_profile(db, current_user.id)
    return MeOut(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at,
        profile=ProfileOut.model_validate(profile),
    )


@router.patch("/me/profile", response_model=ProfileOut)
async def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(_get_db),
) -> ProfileOut:
    profile = await _get_or_create_profile(db, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return ProfileOut.model_validate(profile)


@router.get("/users/{username}", response_model=PublicProfileOut)
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(_get_db),
    viewer_id: Optional[uuid.UUID] = Depends(_optional_viewer_id),
) -> PublicProfileOut:
    res = await db.execute(select(User).where(User.username == username))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile = await _get_or_create_profile(db, user.id)

    if profile.visibility == Visibility.public:
        pass
    else:
        # Require self or friends for friends/private
        if viewer_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if viewer_id != user.id and not await _are_friends(db, viewer_id, user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return PublicProfileOut(username=user.username, profile=ProfileOut.model_validate(profile))

