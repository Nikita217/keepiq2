from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class ProcessingLog(Base, TimestampMixin):
    __tablename__ = "processing_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    incoming_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incoming_items.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(64), index=True)
    level: Mapped[str] = mapped_column(String(16), default="info")
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

    incoming_item = relationship("IncomingItem", back_populates="processing_logs")
