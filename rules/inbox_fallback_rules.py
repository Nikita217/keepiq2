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
                    action=SuggestionActionType.REVIEW_NOW,
                    label="Разобрать сейчас",
                    target_type=IntentType.INBOX_REVIEW,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.SEND_TO_INBOX,
                    label="Оставить во входящих",
                    target_type=IntentType.INBOX_REVIEW,
                ),
            ]
        return result

