from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(Text)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    user: Mapped["User"] = relationship("User")

