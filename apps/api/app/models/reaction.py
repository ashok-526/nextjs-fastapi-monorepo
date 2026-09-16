from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReactionType(str, enum.Enum):
    like = "like"
    love = "love"
    haha = "haha"
    wow = "wow"
    sad = "sad"
    angry = "angry"


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_reactions_post_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[ReactionType] = mapped_column(Enum(ReactionType, name="reaction_type"))

