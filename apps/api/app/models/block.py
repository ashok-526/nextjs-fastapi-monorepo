from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (
        PrimaryKeyConstraint("blocker_id", "blocked_id", name="pk_blocks"),
    )

    blocker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    blocked_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

