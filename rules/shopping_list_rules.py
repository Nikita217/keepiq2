from __future__ import annotations

from utils.text import split_lines_to_items

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisContext, AnalysisItem, StructuredAnalysisResult, StructuredAnalysisSuggestion
from rules.base import DeterministicRule


class ShoppingListRule(DeterministicRule):
    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        text = (context.extracted.raw_text or context.extracted.extracted_text or "").lower()
        if not text.startswith("купить "):
            return result
        items = split_lines_to_items(text.replace("купить ", "", 1))
        if len(items) < 2:
            return result
        result.primary_intent = IntentType.LIST
        result.items = [
            AnalysisItem(
                type=IntentType.LIST,
                title="Список покупок",
                description=context.extracted.extracted_text,
                list_items=items,
                category="shopping",
                needs_confirmation=False,
                metadata={"kind": "shopping"},
            )
        ]
        result.user_action_suggestions = [
            StructuredAnalysisSuggestion(
                action=SuggestionActionType.CREATE_LIST,
                label="Сохранить как список",
                target_item_index=0,
                target_type=IntentType.LIST,
            )
        ]
        return result

