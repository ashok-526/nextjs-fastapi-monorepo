from __future__ import annotations

import enum
from typing import Optional
import uuid

from sqlalchemy import String, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Visibility(str, enum.Enum):
    public = "public"
    friends = "friends"
    private = "private"


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility"), default=Visibility.public, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
