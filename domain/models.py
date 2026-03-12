from __future__ import annotations

from datetime import datetime as DateTime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.enums import ConfidenceLevel, IntentType, SourceType, SuggestionActionType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class NormalizedAttachment(StrictModel):
    telegram_file_id: str | None = None
    telegram_unique_file_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    media_type: str | None = None
    local_path: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None


class NormalizedIncomingPayload(StrictModel):
    incoming_id: str | None = None
    user_id: int
    source_type: SourceType
    raw_text: str | None = None
    caption: str | None = None
    source_url: str | None = None
    media_type: str | None = None
    forwarded: bool = False
    original_message_id: int | None = None
    original_chat_id: int | None = None
    original_caption: str | None = None
    attachments: list[NormalizedAttachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedContent(StrictModel):
    raw_text: str | None = None
    extracted_text: str | None = None
    transcript: str | None = None
    ocr_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_signals: list[str] = Field(default_factory=list)
    extraction_errors: list[str] = Field(default_factory=list)
    ambiguous_datetime_phrases: list[str] = Field(default_factory=list)


class ExtractedEntities(StrictModel):
    dates: list[str] = Field(default_factory=list)
    times: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    ambiguous_datetimes: list[str] = Field(default_factory=list)


class AnalysisItem(StrictModel):
    type: IntentType
    title: str
    description: str | None = None
    datetime: DateTime | None = None
    date_only: bool = False
    priority: str = "medium"
    category: str | None = None
    people: list[str] = Field(default_factory=list)
    places: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    list_items: list[str] = Field(default_factory=list)
    needs_confirmation: bool = False
    uncertain_fields: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuredAnalysisSuggestion(StrictModel):
    action: SuggestionActionType
    label: str
    target_item_index: int | None = None
    target_type: IntentType | None = None
    scheduled_for: DateTime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisTrace(StrictModel):
    provider: str
    model: str | None = None
    prompt_version: str = "v1"
    fallback_used: bool = False
    raw_response: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class StructuredAnalysisResult(StrictModel):
    source_type: SourceType
    detected_language: str | None = None
    summary: str
    primary_intent: IntentType
    confidence: float
    confidence_level: ConfidenceLevel | None = None
    items: list[AnalysisItem] = Field(default_factory=list)
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    user_action_suggestions: list[StructuredAnalysisSuggestion] = Field(default_factory=list)
    should_store_original: bool = True
    should_go_to_inbox: bool = False
    reasoning_notes: str | None = None
    trace: AnalysisTrace = Field(default_factory=lambda: AnalysisTrace(provider="unknown"))

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value

    @model_validator(mode="after")
    def _sync_inbox_intent(self) -> "StructuredAnalysisResult":
        if self.primary_intent == IntentType.INBOX_REVIEW:
            self.should_go_to_inbox = True
        return self


class AnalysisContext(StrictModel):
    now: DateTime
    timezone: str
    payload: NormalizedIncomingPayload
    extracted: ExtractedContent
