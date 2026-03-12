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
            result = self._apply_suggestion(result, selected_suggestion)
        elif target_type:
            result = self._coerce_result(item, result, target_type, title)
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
        if target and suggestion.scheduled_for:
            target.datetime = suggestion.scheduled_for
            target.date_only = False
            if suggestion.target_type == IntentType.REPLY_LATER:
                target.type = IntentType.REPLY_LATER
            elif suggestion.target_type == IntentType.REMINDER and target.type == IntentType.TASK:
                target.needs_confirmation = False
            elif suggestion.target_type and suggestion.target_type != IntentType.REMINDER:
                target.type = suggestion.target_type
        if suggestion.action == SuggestionActionType.KEEP_ONLY_TASKS:
            result.items = [item for item in result.items if item.type == IntentType.TASK]
            result.primary_intent = IntentType.TASK if result.items else IntentType.INBOX_REVIEW
        elif suggestion.action == SuggestionActionType.CREATE_LIST and target:
            target.type = IntentType.LIST
            result.primary_intent = IntentType.LIST
        elif suggestion.action == SuggestionActionType.SAVE_ONLY and target:
            target.type = IntentType.SAVE_ONLY
            result.primary_intent = IntentType.SAVE_ONLY
        elif suggestion.target_type and suggestion.target_type != IntentType.REMINDER:
            result.primary_intent = suggestion.target_type
        result.should_go_to_inbox = False
        for item in result.items:
            item.needs_confirmation = False
        return result

    def _coerce_result(
        self,
        item: IncomingItem,
        result: StructuredAnalysisResult,
        target_type: str,
        title: str | None,
    ) -> StructuredAnalysisResult:
        intent = IntentType(target_type)
        if result.items:
            result.items[0].type = intent
            if title:
                result.items[0].title = title
        else:
            result.items = [
                AnalysisItem(
                    type=intent,
                    title=title or item.summary or compact_text(item.raw_text or item.extracted_text or "Объект"),
                    description=compact_text(item.raw_text or item.extracted_text or item.summary),
                    datetime=self._first_datetime(item),
                    needs_confirmation=False,
                )
            ]
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

