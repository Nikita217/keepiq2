from __future__ import annotations

from datetime import timedelta

from domain.enums import IntentType, SourceType, SuggestionActionType
from domain.models import AnalysisContext, AnalysisItem, StructuredAnalysisResult, StructuredAnalysisSuggestion
from rules.base import DeterministicRule


class TicketRule(DeterministicRule):
    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        is_ticket_like = context.payload.source_type in {SourceType.TICKET, SourceType.BOOKING_CONFIRMATION} or (
            context.extracted.metadata.get("document_hint") == "ticket_or_booking"
        )
        if not is_ticket_like:
            return result

        if not result.items:
            result.items = [
                AnalysisItem(
                    type=IntentType.EVENT,
                    title="Событие из билета",
                    description=context.extracted.extracted_text,
                    needs_confirmation=True,
                    metadata={"ticket_like": True},
                )
            ]
        else:
            result.items[0].type = IntentType.EVENT
            result.items[0].metadata["ticket_like"] = True

        result.primary_intent = IntentType.EVENT
        result.should_store_original = True
        suggestions = list(result.user_action_suggestions)
        primary = result.items[0]
        if primary.datetime:
            suggestions.extend(
                [
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="За день",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime - timedelta(days=1),
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="За 3 часа",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime - timedelta(hours=3),
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="Утром в день события",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime.replace(hour=9, minute=0, second=0, microsecond=0),
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_EVENT,
                        label="Сохранить событие",
                        target_item_index=0,
                        target_type=IntentType.EVENT,
                    ),
                ]
            )
        result.user_action_suggestions = suggestions[:4]
        return result

