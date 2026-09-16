from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt, JoseError

from app.core.config import get_settings
from app.app.db.session import get_session
from app.models.user import User


async def get_db() -> AsyncSession:
    async for s in get_session():
        return s  # pragma: no cover


async def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    db: AsyncSession = Depends(get_db),
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
        # Validate exp, iat if present
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

