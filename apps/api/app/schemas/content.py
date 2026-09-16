from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.profile import Visibility
from app.models.reaction import ReactionType


class PostCreate(BaseModel):
    body: str = Field(min_length=1)
    media_json: Optional[Dict[str, Any]] = None
    visibility: Visibility


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    body: str
    media_json: Optional[Dict[str, Any]] = None
    visibility: Visibility
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReactionCreate(BaseModel):
    type: ReactionType


class ReactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: ReactionType


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    parent_comment_id: Optional[UUID] = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    author_id: UUID
    parent_comment_id: Optional[UUID] = None
    body: str
    created_at: Optional[datetime] = None
    depth: int = 0

