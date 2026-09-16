from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Enum, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from .profile import Visibility


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    media_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility, name="visibility"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    author: Mapped["User"] = relationship("User")

