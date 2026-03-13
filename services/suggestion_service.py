from __future__ import annotations

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisContext, StructuredAnalysisResult, StructuredAnalysisSuggestion


class SuggestionService:
    def build(self, context: AnalysisContext, result: StructuredAnalysisResult) -> list[StructuredAnalysisSuggestion]:
        suggestions = list(result.user_action_suggestions)
        if suggestions:
            return suggestions[:4]
        if result.primary_intent == IntentType.INBOX_REVIEW or result.should_go_to_inbox:
            return self._fallback_type_choices()
        if result.primary_intent == IntentType.LIST:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_LIST,
                    label="Сохранить как список",
                    target_item_index=0,
                    target_type=IntentType.LIST,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить заметкой",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                ),
            ]
        if result.primary_intent == IntentType.NOTE:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить в идеи" if self._is_idea(result) else "Сохранить заметку",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_LIST,
                    label="Сделать списком",
                    target_item_index=0,
                    target_type=IntentType.LIST,
                ),
            ]
        if result.primary_intent == IntentType.REMINDER:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_REMINDER,
                    label="Сохранить напоминание",
                    target_item_index=0,
                    target_type=IntentType.REMINDER,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить заметкой",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_LIST,
                    label="Сделать списком",
                    target_item_index=0,
                    target_type=IntentType.LIST,
                ),
            ]
        if result.primary_intent == IntentType.EVENT:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_EVENT,
                    label="Сохранить событие",
                    target_item_index=0,
                    target_type=IntentType.EVENT,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить заметкой",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                ),
            ]
        return suggestions[:4]

    def _is_idea(self, result: StructuredAnalysisResult) -> bool:
        return bool(result.items and result.items[0].category == "ideas")

    def _fallback_type_choices(self) -> list[StructuredAnalysisSuggestion]:
        return [
            StructuredAnalysisSuggestion(
                action=SuggestionActionType.CREATE_REMINDER,
                label="Это напоминание",
                target_type=IntentType.REMINDER,
            ),
            StructuredAnalysisSuggestion(
                action=SuggestionActionType.CREATE_LIST,
                label="Это список",
                target_type=IntentType.LIST,
            ),
            StructuredAnalysisSuggestion(
                action=SuggestionActionType.CREATE_EVENT,
                label="Это событие",
                target_type=IntentType.EVENT,
            ),
            StructuredAnalysisSuggestion(
                action=SuggestionActionType.CREATE_NOTE,
                label="Это заметка",
                target_type=IntentType.NOTE,
            ),
        ]

