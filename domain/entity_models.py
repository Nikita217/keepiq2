from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from domain.analysis_models import StrictModel
from domain.enums import FinalType


class EntityDraft(StrictModel):
    type: FinalType
    title: str
    description: str | None = None
    list_items: list[str] = Field(default_factory=list)
    scheduled_at: datetime | None = None
    scheduled_date: date | None = None
    event_datetime: datetime | None = None
    source_item_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
