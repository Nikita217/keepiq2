from __future__ import annotations

from domain.enums import ConfidenceLevel, IntentType, SuggestionActionType
from domain.models import AnalysisContext, StructuredAnalysisResult, StructuredAnalysisSuggestion
from rules.base import DeterministicRule


class InboxFallbackRule(DeterministicRule):
    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        no_useful_text = not (context.extracted.extracted_text or "").strip()
        poor_extraction = bool(context.extracted.extraction_errors) and no_useful_text
        if result.confidence_level == ConfidenceLevel.LOW or no_useful_text or poor_extraction:
            result.primary_intent = IntentType.INBOX_REVIEW
            result.items = []
            result.should_go_to_inbox = True
            result.should_store_original = True
            result.summary = result.summary or "Недостаточно данных для уверенного разбора"
            result.user_action_suggestions = [
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
        return result

