from __future__ import annotations

from datetime import datetime
from uuid import UUID

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisItem, StructuredAnalysisResult, StructuredAnalysisSuggestion
from models import IncomingItem, ProcessingLog
from models.enums import ParseStatus
from repositories.incoming import IncomingRepository
from services.object_builder import ObjectBuilderService
from utils.text import compact_text


class InboxActionService:
    def __init__(self, session) -> None:
        self.session = session
        self.repo = IncomingRepository(session)
        self.builder = ObjectBuilderService(session)

    async def resolve(
        self,
        *,
        item_id: UUID,
        user_id: int | None = None,
        target_type: str | None = None,
        title: str | None = None,
        description: str | None = None,
        scheduled_at: datetime | None = None,
        kind: str | None = None,
        source_url: str | None = None,
        list_items: list[str] | None = None,
        force_confirmation: bool = False,
        suggested_action_id: int | None = None,
    ) -> IncomingItem:
        item = await self.repo.get(item_id)
        if item is None:
            raise LookupError("item not found")
        if user_id is not None and item.user_id != user_id:
            raise PermissionError("item does not belong to user")

        result = self._result_for_item(item)
        selected_suggestion: StructuredAnalysisSuggestion | None = None

        if suggested_action_id is not None and 0 <= suggested_action_id < len(result.user_action_suggestions):
            selected_suggestion = result.user_action_suggestions[suggested_action_id]
            result = self._apply_suggestion(item, result, selected_suggestion)
        elif target_type:
            result = self._coerce_result(
                item,
                result,
                target_type,
                title,
                description=description,
                scheduled_at=scheduled_at,
                kind=kind,
                source_url=source_url,
                list_items=list_items,
            )
        elif title and result.items:
            result.items[0].title = title
            result.summary = title

        created_links = []
        if result.primary_intent != IntentType.INBOX_REVIEW:
            created_links = await self.builder.materialize(
                user_id=item.user_id,
                incoming_item_id=item.id,
                result=result,
                selected_suggestion=selected_suggestion,
                upsert=True,
            )

        item.proposed_type = result.primary_intent.value
        item.summary = result.summary
        item.needs_confirmation = force_confirmation
        item.parse_status = ParseStatus.NEEDS_REVIEW.value if force_confirmation else ParseStatus.CONFIRMED.value
        item.analysis_result_json = result.model_dump(mode="json")
        item.linked_objects_json = [{"object_type": link.object_type, "object_id": link.object_id} for link in created_links]
        metadata = dict(item.metadata_json or {})
        metadata.update(
            {
                "assistant_response": metadata.get("assistant_response") or result.summary,
                "resolved_object_type": target_type or result.primary_intent.value,
                "suggested_actions": [action.model_dump(mode="json") for action in result.user_action_suggestions],
                "last_selected_action": selected_suggestion.label if selected_suggestion else (target_type or "Сохранить"),
            }
        )
        item.metadata_json = metadata
        await self.repo.add_log(
            ProcessingLog(
                incoming_item_id=item.id,
                stage="resolve",
                message=f"Resolved as {target_type or result.primary_intent.value}",
                payload_json=result.model_dump(mode="json"),
            )
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item

    def _result_for_item(self, item: IncomingItem) -> StructuredAnalysisResult:
        raw = item.analysis_result_json or {"source_type": item.incoming_type}
        return StructuredAnalysisResult.model_validate(raw)

    def _apply_suggestion(
        self,
        item: IncomingItem,
        result: StructuredAnalysisResult,
        suggestion: StructuredAnalysisSuggestion,
    ) -> StructuredAnalysisResult:
        target = self._target_item(result, suggestion)
        if suggestion.action == SuggestionActionType.REVIEW_NOW:
            result.should_go_to_inbox = False
            return result
        if suggestion.action == SuggestionActionType.SEND_TO_INBOX:
            result.primary_intent = IntentType.INBOX_REVIEW
            result.should_go_to_inbox = True
            result.items = []
            return result
        if target is None and suggestion.target_type:
            result = self._coerce_result(
                item,
                result,
                suggestion.target_type.value,
                item.summary,
                description=compact_text(item.raw_text or item.extracted_text or item.summary),
                scheduled_at=suggestion.scheduled_for,
                kind=None,
                source_url=item.source_url,
                list_items=None,
            )
            target = result.items[0] if result.items else None
        if target and suggestion.scheduled_for:
            target.datetime = suggestion.scheduled_for
            target.date_only = False
        if target and suggestion.target_type and suggestion.action != SuggestionActionType.CREATE_REMINDER:
            target.type = suggestion.target_type
        if suggestion.action == SuggestionActionType.KEEP_ONLY_TASKS:
            result.items = [entry for entry in result.items if entry.type == IntentType.REMINDER]
            result.primary_intent = IntentType.REMINDER if result.items else IntentType.INBOX_REVIEW
        elif suggestion.action == SuggestionActionType.CREATE_REMINDER:
            if target and target.type == IntentType.REMINDER:
                result.primary_intent = IntentType.REMINDER
        elif suggestion.target_type:
            result.primary_intent = suggestion.target_type
        result.should_go_to_inbox = False
        for entry in result.items:
            entry.needs_confirmation = False
        result.summary = result.items[0].title if result.items else result.summary
        return result

    def _coerce_result(
        self,
        item: IncomingItem,
        result: StructuredAnalysisResult,
        target_type: str,
        title: str | None,
        *,
        description: str | None,
        scheduled_at: datetime | None,
        kind: str | None,
        source_url: str | None,
        list_items: list[str] | None,
    ) -> StructuredAnalysisResult:
        intent = IntentType(target_type)
        if result.items:
            target = result.items[0]
            target.type = intent
            if title:
                target.title = title
            if description is not None:
                target.description = description
            if scheduled_at is not None or intent in {IntentType.REMINDER, IntentType.EVENT}:
                target.datetime = scheduled_at
                target.date_only = False
            if list_items is not None and intent == IntentType.LIST:
                target.list_items = list_items
            if kind:
                target.category = kind
                target.metadata["kind"] = kind
            if source_url:
                target.links = [source_url]
                target.metadata["url"] = source_url
        else:
            target = AnalysisItem(
                type=intent,
                title=title or item.summary or compact_text(item.raw_text or item.extracted_text or "Объект"),
                description=description if description is not None else compact_text(item.raw_text or item.extracted_text or item.summary),
                datetime=scheduled_at or self._first_datetime(item),
                needs_confirmation=False,
                list_items=list_items or [],
                category=kind,
                links=[source_url] if source_url else [],
                metadata={key: value for key, value in {"kind": kind, "url": source_url}.items() if value},
            )
            result.items = [target]
        result.primary_intent = intent
        result.summary = title or result.summary or item.summary or result.items[0].title
        result.should_go_to_inbox = False
        for analysis_item in result.items:
            analysis_item.needs_confirmation = False
        return result

    def _target_item(self, result: StructuredAnalysisResult, suggestion: StructuredAnalysisSuggestion) -> AnalysisItem | None:
        if not result.items:
            return None
        if suggestion.target_item_index is None:
            return result.items[0]
        if 0 <= suggestion.target_item_index < len(result.items):
            return result.items[suggestion.target_item_index]
        return result.items[0]

    def _first_datetime(self, item: IncomingItem) -> datetime | None:
        parsed = (item.parsed_entities_json or {}).get("dates")
        if not parsed:
            return None
        try:
            return datetime.fromisoformat(parsed[0])
        except ValueError:
            return None

