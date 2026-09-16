from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    post: Mapped["Post"] = relationship("Post")
    author: Mapped["User"] = relationship("User")
    parent: Mapped["Comment" | None] = relationship("Comment", remote_side="Comment.id")

