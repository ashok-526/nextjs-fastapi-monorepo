from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.profile import Visibility


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    visibility: Visibility


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    cover_url: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    visibility: Optional[Visibility] = Field(default=None)


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    created_at: Optional[datetime] = None
    profile: ProfileOut


class PublicProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    profile: ProfileOut

