from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, DateTime, ForeignKey, String, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    blocked = "blocked"


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendships_requester_addressee"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    addressee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[FriendshipStatus] = mapped_column(Enum(FriendshipStatus, name="friendship_status"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

