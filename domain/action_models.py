from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from domain.analysis_models import StrictModel
from domain.entity_models import EntityDraft
from domain.enums import ActionKind, FinalType


class ActionSuggestion(StrictModel):
    label: str
    action: ActionKind
    target_type: FinalType | None = None
    scheduled_for: datetime | None = None
    items: list[EntityDraft] = Field(default_factory=list)
    response_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
