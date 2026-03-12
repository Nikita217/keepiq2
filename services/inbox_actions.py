from __future__ import annotations

from datetime import datetime
from uuid import UUID

from models import IncomingItem, ProcessingLog
from models.enums import ParseStatus
from repositories.incoming import IncomingRepository
from schemas.ai import AnalysisPayload, CandidateObject, SuggestedAction
from services.object_builder import ObjectBuilderService
from utils.text import compact_text, split_lines_to_items


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

        payload = await self._payload_for_item(item)
        chosen_action: SuggestedAction | None = None

        if suggested_action_id is not None and 0 <= suggested_action_id < len(payload.suggested_actions):
            chosen_action = payload.suggested_actions[suggested_action_id]
            payload = self._apply_suggested_action(item, payload, chosen_action)
        elif target_type:
            payload = self._coerce_payload(item, payload, target_type, title)
        elif title and payload.candidates:
            payload.candidates[0].title = title

        if payload.proposed_type != "answer" or payload.candidates:
            await self.builder.materialize(
                user_id=item.user_id,
                incoming_item_id=item.id,
                payload=payload,
                upsert=True,
            )

        item.proposed_type = payload.proposed_type
        item.summary = title or payload.summary or item.summary
        item.needs_confirmation = force_confirmation
        item.parse_status = ParseStatus.NEEDS_REVIEW.value if force_confirmation else ParseStatus.CONFIRMED.value
        metadata = dict(item.metadata_json or {})
        metadata.update(
            {
                "assistant_response": payload.assistant_response,
                "clarification_question": payload.clarification_question,
                "resolved_object_type": target_type or payload.proposed_type,
                "suggested_actions": [action.model_dump(mode="json") for action in payload.suggested_actions],
                "last_selected_action": chosen_action.label if chosen_action else None,
            }
        )
        item.metadata_json = metadata
        await self.repo.add_log(
            ProcessingLog(
                incoming_item_id=item.id,
                stage="resolve",
                message=f"Resolved as {target_type or payload.proposed_type}",
                payload_json=payload.model_dump(mode="json"),
            )
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def _payload_for_item(self, item: IncomingItem) -> AnalysisPayload:
        latest = await self.repo.get_latest_analysis(item.id)
        if latest and latest.result_json:
            try:
                return AnalysisPayload(**latest.result_json)
            except Exception:
                pass
        fallback_type = item.proposed_type or "note"
        return self._coerce_payload(item, None, fallback_type, None)

    def _apply_suggested_action(
        self,
        item: IncomingItem,
        payload: AnalysisPayload,
        action: SuggestedAction,
    ) -> AnalysisPayload:
        if action.target_type and action.target_type != payload.proposed_type:
            payload = self._coerce_payload(item, payload, action.target_type, action.title)
        elif action.title and payload.candidates:
            payload.candidates[0].title = action.title
            payload.summary = action.title

        for candidate in payload.candidates:
            if action.target_type == "task" or candidate.object_type == "task":
                if action.due_at is not None:
                    candidate.due_at = action.due_at
            if action.target_type == "reminder" or candidate.object_type == "reminder":
                if action.remind_at is not None:
                    candidate.remind_at = action.remind_at
                elif action.due_at is not None and candidate.object_type == "reminder":
                    candidate.remind_at = action.due_at
            if action.target_type == "event" or candidate.object_type == "event":
                if action.event_at is not None:
                    candidate.event_at = action.event_at
            if action.target_type == "reply_later" or candidate.object_type == "reply_later":
                if action.due_at is not None:
                    candidate.due_at = action.due_at

        if action.remind_at is not None:
            for candidate in payload.candidates:
                if candidate.object_type == "task" and candidate.metadata.get("linked_to") == "reminder":
                    candidate.due_at = action.remind_at
        if action.event_at is not None:
            for candidate in payload.candidates:
                if candidate.object_type == "reminder" and candidate.metadata.get("linked_to") == "event":
                    candidate.remind_at = action.event_at

        payload.needs_confirmation = False
        if action.response_text:
            payload.assistant_response = action.response_text
        return payload

    def _coerce_payload(
        self,
        item: IncomingItem,
        payload: AnalysisPayload | None,
        target_type: str,
        title: str | None,
    ) -> AnalysisPayload:
        source_text = compact_text(item.raw_text or item.transcript_text or item.ocr_text or item.summary)
        if payload is not None:
            matching = [candidate for candidate in payload.candidates if candidate.object_type == target_type]
            if matching:
                payload.proposed_type = target_type
                payload.needs_confirmation = False
                payload.confidence = max(payload.confidence, 0.99)
                payload.candidates = matching
                if title:
                    payload.candidates[0].title = title
                    payload.summary = title
                return payload

        first_dt = None
        for entity in item.entities:
            if entity.entity_type == "datetime" and entity.value:
                first_dt = entity.normalized_value or entity.value
                break

        candidate_title = title or item.summary or source_text[:100] or target_type
        candidate_items = split_lines_to_items(source_text) if target_type == "list" else []
        metadata = {"manual": True}
        candidate = CandidateObject(
            object_type=target_type,
            title=candidate_title,
            description=source_text,
            items=candidate_items,
            metadata=metadata,
        )
        if first_dt:
            parsed_dt = datetime.fromisoformat(first_dt)
            if target_type == "task":
                candidate.due_at = parsed_dt
            elif target_type == "reminder":
                candidate.remind_at = parsed_dt
            elif target_type == "event":
                candidate.event_at = parsed_dt
            elif target_type == "reply_later":
                candidate.due_at = parsed_dt

        assistant_response = None
        if target_type == "answer":
            assistant_response = (item.metadata_json or {}).get("assistant_response") or source_text

        return AnalysisPayload(
            provider="manual",
            model=None,
            summary=candidate_title,
            proposed_type=target_type,
            confidence=1.0,
            needs_confirmation=False,
            extracted_entities=[],
            candidates=[] if target_type == "answer" else [candidate],
            draft_replies={},
            assistant_response=assistant_response,
            clarification_question=None,
            suggested_actions=[],
            raw={"manual": True},
        )
