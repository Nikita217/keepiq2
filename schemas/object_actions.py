from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ObjectConvertRequest(BaseModel):
    source_type: str
    source_id: UUID
    target_type: str
    title: str | None = None
    description: str | None = None
    scheduled_at: datetime | None = None
    kind: str | None = None
    source_url: str | None = None
    list_items: list[str] = Field(default_factory=list)


class ObjectConvertResponse(BaseModel):
    object_type: str
    object_id: UUID
