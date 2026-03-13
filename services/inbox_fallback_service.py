from __future__ import annotations

from domain.action_models import ActionSuggestion
from domain.entity_models import EntityDraft
from domain.enums import ActionKind, FinalType


class InboxFallbackService:
    def keep_in_inbox_action(self, drafts: list[EntityDraft] | None = None) -> ActionSuggestion:
        return ActionSuggestion(
            label="Оставить во входящих",
            action=ActionKind.KEEP_IN_INBOX,
            target_type=None,
            scheduled_for=None,
            items=drafts or [],
            response_text="Оставил во входящих.",
        )

    def note_action(self, drafts: list[EntityDraft]) -> ActionSuggestion:
        note_drafts = [
            EntityDraft(
                type=FinalType.NOTE,
                title=drafts[0].title if drafts else "Заметка",
                description=drafts[0].description if drafts else None,
                list_items=[],
                metadata=drafts[0].metadata if drafts else {},
            )
        ]
        return ActionSuggestion(
            label="Сохранить заметкой",
            action=ActionKind.CREATE,
            target_type=FinalType.NOTE,
            items=note_drafts,
            response_text="Сохранил заметкой.",
        )
