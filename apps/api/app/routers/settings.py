from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps import get_current_user
from app.models.user import User
from app.services.notifications import get_redis
from app.models.profile import Visibility


router = APIRouter(prefix="/settings", tags=["settings"])


class PrivacySettings(BaseModel):
    default_post_visibility: Visibility = Field(default=Visibility.public)


@router.get("/privacy", response_model=PrivacySettings)
async def get_privacy(current_user: User = Depends(get_current_user)) -> PrivacySettings:
    r = await get_redis()
    key = f"user:{current_user.id}:default_visibility"
    raw = await r.get(key)
    if raw:
        v = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        try:
            return PrivacySettings(default_post_visibility=Visibility(v))
        except Exception:
            pass
    return PrivacySettings()


@router.patch("/privacy", response_model=PrivacySettings)
async def set_privacy(payload: PrivacySettings, current_user: User = Depends(get_current_user)) -> PrivacySettings:
    r = await get_redis()
    key = f"user:{current_user.id}:default_visibility"
    await r.setex(key, 7 * 24 * 3600, payload.default_post_visibility.value)
    return payload

