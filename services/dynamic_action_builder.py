from __future__ import annotations

from datetime import datetime

from domain.action_models import ActionSuggestion
from domain.analysis_models import ResolvedAnalysisResult
from domain.entity_models import EntityDraft
from domain.enums import ActionKind, ConfidenceLevel, FinalType
from rules.datetime_suggestion_rules import combine_date_and_time, default_event_times, default_reminder_times, format_time_label, human_date_label
from services.inbox_fallback_service import InboxFallbackService


class DynamicActionBuilder:
    def __init__(self) -> None:
        self.fallback = InboxFallbackService()

    def build(self, result: ResolvedAnalysisResult, drafts: list[EntityDraft], now: datetime) -> list[ActionSuggestion]:
        if result.confidence_level == ConfidenceLevel.LOW:
            actions = []
            if drafts and result.primary_type == FinalType.NOTE:
                actions.append(self._note_action(drafts[0]))
            elif drafts:
                actions.append(self.fallback.note_action(drafts))
            actions.append(self.fallback.keep_in_inbox_action(drafts))
            return actions[:4]

        if not drafts:
            return [self.fallback.keep_in_inbox_action([])]

        if result.primary_type == FinalType.REMINDER:
            return self._build_reminder_actions(drafts, now)
        if result.primary_type == FinalType.LIST:
            return self._build_list_actions(drafts)
        if result.primary_type == FinalType.EVENT:
            return self._build_event_actions(drafts, now)
        return self._build_note_actions(result, drafts)

    def _build_reminder_actions(self, drafts: list[EntityDraft], now: datetime) -> list[ActionSuggestion]:
        first = drafts[0]
        if first.scheduled_at:
            label = f"Напомнить {human_date_label(first.scheduled_at.date(), today=now.date())} в {first.scheduled_at.strftime('%H:%M')}"
            return [
                ActionSuggestion(
                    label=label,
                    action=ActionKind.CREATE,
                    target_type=FinalType.REMINDER,
                    scheduled_for=first.scheduled_at,
                    items=drafts,
                    response_text="Напоминание создано.",
                ),
                self.fallback.note_action(drafts),
                self.fallback.keep_in_inbox_action(drafts),
            ]
        if first.scheduled_date:
            actions = []
            for point in default_reminder_times():
                scheduled_for = combine_date_and_time(first.scheduled_date, point, now.tzinfo)
                action_drafts = [draft.model_copy(update={"scheduled_at": scheduled_for}) for draft in drafts]
                actions.append(
                    ActionSuggestion(
                        label=f"Напомнить {human_date_label(first.scheduled_date, today=now.date())} в {format_time_label(point)}",
                        action=ActionKind.CREATE,
                        target_type=FinalType.REMINDER,
                        scheduled_for=scheduled_for,
                        items=action_drafts,
                        response_text="Напоминание создано.",
                    )
                )
            actions.append(self.fallback.keep_in_inbox_action(drafts))
            return actions[:4]
        return [self.fallback.note_action(drafts), self.fallback.keep_in_inbox_action(drafts)]

    def _build_list_actions(self, drafts: list[EntityDraft]) -> list[ActionSuggestion]:
        primary = drafts[0]
        return [
            ActionSuggestion(
                label="Сохранить списком",
                action=ActionKind.CREATE,
                target_type=FinalType.LIST,
                items=[primary],
                response_text="Список сохранён.",
            ),
            self._note_action(primary),
            self.fallback.keep_in_inbox_action(drafts),
        ]

    def _build_event_actions(self, drafts: list[EntityDraft], now: datetime) -> list[ActionSuggestion]:
        draft = drafts[0]
        if draft.scheduled_at:
            date_label = human_date_label(draft.scheduled_at.date(), today=now.date())
            return [
                ActionSuggestion(
                    label=f"Создать событие {date_label} в {draft.scheduled_at.strftime('%H:%M')}",
                    action=ActionKind.CREATE,
                    target_type=FinalType.EVENT,
                    scheduled_for=draft.scheduled_at,
                    items=[draft],
                    response_text="Событие создано.",
                ),
                ActionSuggestion(
                    label=f"Создать событие {date_label}",
                    action=ActionKind.CREATE,
                    target_type=FinalType.EVENT,
                    items=[draft.model_copy(update={"scheduled_at": None})],
                    response_text="Событие создано.",
                ),
                self._note_action(draft),
                self.fallback.keep_in_inbox_action(drafts),
            ]
        if draft.scheduled_date:
            actions = [
                ActionSuggestion(
                    label=f"Создать событие {human_date_label(draft.scheduled_date, today=now.date())}",
                    action=ActionKind.CREATE,
                    target_type=FinalType.EVENT,
                    items=[draft],
                    response_text="Событие создано.",
                )
            ]
            for point in default_event_times():
                scheduled_for = combine_date_and_time(draft.scheduled_date, point, now.tzinfo)
                actions.append(
                    ActionSuggestion(
                        label=f"Создать событие {human_date_label(draft.scheduled_date, today=now.date())} в {format_time_label(point)}",
                        action=ActionKind.CREATE,
                        target_type=FinalType.EVENT,
                        scheduled_for=scheduled_for,
                        items=[draft.model_copy(update={"scheduled_at": scheduled_for})],
                        response_text="Событие создано.",
                    )
                )
            actions.append(self.fallback.keep_in_inbox_action(drafts))
            return actions[:4]
        return [self._note_action(draft), self.fallback.keep_in_inbox_action(drafts)]

    def _build_note_actions(self, result: ResolvedAnalysisResult, drafts: list[EntityDraft]) -> list[ActionSuggestion]:
        primary = drafts[0]
        actions = [self._note_action(primary)]
        if result.secondary_candidate_type == FinalType.LIST and primary.list_items:
            actions.append(
                ActionSuggestion(
                    label="Сохранить списком",
                    action=ActionKind.CREATE,
                    target_type=FinalType.LIST,
                    items=[primary.model_copy(update={"type": FinalType.LIST})],
                    response_text="Список сохранён.",
                )
            )
        actions.append(self.fallback.keep_in_inbox_action(drafts))
        return actions[:4]

    def _note_action(self, draft: EntityDraft) -> ActionSuggestion:
        return ActionSuggestion(
            label="Сохранить заметкой",
            action=ActionKind.CREATE,
            target_type=FinalType.NOTE,
            items=[draft.model_copy(update={"type": FinalType.NOTE})],
            response_text="Заметка сохранена.",
        )
