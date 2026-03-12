from __future__ import annotations

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisContext, StructuredAnalysisResult, StructuredAnalysisSuggestion


class SuggestionService:
    def build(self, context: AnalysisContext, result: StructuredAnalysisResult) -> list[StructuredAnalysisSuggestion]:
        suggestions = list(result.user_action_suggestions)
        if suggestions:
            return suggestions[:4]
        if result.primary_intent == IntentType.LIST:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_LIST,
                    label="Сохранить как список",
                    target_item_index=0,
                    target_type=IntentType.LIST,
                )
            ]
        if result.primary_intent == IntentType.NOTE:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить в идеи" if self._is_idea(result) else "Сохранить заметку",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                )
            ]
        if result.primary_intent == IntentType.SAVE_ONLY:
            return [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.SAVE_ONLY,
                    label="Просто сохранить",
                    target_item_index=0,
                    target_type=IntentType.SAVE_ONLY,
                )
            ]
        return suggestions[:4]

    def _is_idea(self, result: StructuredAnalysisResult) -> bool:
        return bool(result.items and result.items[0].category == "ideas")

