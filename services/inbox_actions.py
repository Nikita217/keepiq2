from __future__ import annotations

from datetime import datetime
from uuid import UUID

from domain.action_models import ActionSuggestion
from domain.entity_models import EntityDraft
from domain.enums import ActionKind, FinalType
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

        action = self._resolve_action(
            item,
            suggested_action_id=suggested_action_id,
            target_type=target_type,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            kind=kind,
            source_url=source_url,
            list_items=list_items,
        )

        created_links = []
        if action.action != ActionKind.KEEP_IN_INBOX:
            created_links = await self.builder.materialize_action(
                user_id=item.user_id,
                incoming_item_id=item.id,
                action=action,
                upsert=True,
            )
            item.parse_status = ParseStatus.CONFIRMED.value
            item.needs_confirmation = False
            item.proposed_type = action.target_type.value if action.target_type else item.proposed_type
            item.summary = action.items[0].title if action.items else item.summary
        else:
            item.parse_status = ParseStatus.NEEDS_REVIEW.value
            item.needs_confirmation = True

        item.linked_objects_json = [{"object_type": link.object_type, "object_id": link.object_id} for link in created_links]
        metadata = dict(item.metadata_json or {})
        metadata["last_selected_action"] = action.label
        metadata["assistant_response"] = action.response_text or metadata.get("assistant_response") or item.summary
        item.metadata_json = metadata
        if force_confirmation:
            item.parse_status = ParseStatus.NEEDS_REVIEW.value
            item.needs_confirmation = True
        await self.repo.add_log(
            ProcessingLog(
                incoming_item_id=item.id,
                stage="resolve",
                message=f"Resolved as {action.target_type.value if action.target_type else 'inbox'}",
                payload_json=action.model_dump(mode="json"),
            )
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item

    def _resolve_action(
        self,
        item: IncomingItem,
        *,
        suggested_action_id: int | None,
        target_type: str | None,
        title: str | None,
        description: str | None,
        scheduled_at: datetime | None,
        kind: str | None,
        source_url: str | None,
        list_items: list[str] | None,
    ) -> ActionSuggestion:
        metadata = dict(item.metadata_json or {})
        if suggested_action_id is not None:
            actions = [ActionSuggestion.model_validate(action) for action in metadata.get("suggested_actions", [])]
            if 0 <= suggested_action_id < len(actions):
                return actions[suggested_action_id]
            raise LookupError("suggested action not found")

        if target_type == "inbox_review":
            return ActionSuggestion(label="Оставить во входящих", action=ActionKind.KEEP_IN_INBOX, items=[])

        if target_type is None:
            raise LookupError("action is not specified")

        final_type = FinalType(target_type)
        body = description if description is not None else compact_text(item.raw_text or item.extracted_text or item.summary)
        draft = EntityDraft(
            type=final_type,
            title=title or item.summary or compact_text(item.raw_text or item.extracted_text or "Объект"),
            description=body,
            list_items=list_items or [],
            scheduled_at=scheduled_at,
            scheduled_date=scheduled_at.date() if scheduled_at else None,
            metadata={
                key: value
                for key, value in {
                    "kind": kind,
                    "source_url": source_url,
                }.items()
                if value is not None
            },
        )
        return ActionSuggestion(
            label=self._label_for_type(final_type),
            action=ActionKind.CREATE,
            target_type=final_type,
            scheduled_for=scheduled_at,
            items=[draft],
            response_text="Готово.",
        )

    def _label_for_type(self, final_type: FinalType) -> str:
        return {
            FinalType.REMINDER: "Сохранить напоминанием",
            FinalType.LIST: "Сохранить списком",
            FinalType.EVENT: "Сохранить событием",
            FinalType.NOTE: "Сохранить заметкой",
        }[final_type]
