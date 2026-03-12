from __future__ import annotations

from domain.enums import ConfidenceLevel, IntentType
from domain.models import StructuredAnalysisResult


class InboxFallbackService:
    def build_message(self, result: StructuredAnalysisResult) -> str:
        if result.confidence_level == ConfidenceLevel.LOW or result.should_go_to_inbox:
            return "Я сохранил это во входящие, чтобы не потерять. Можешь потом выбрать, как лучше оформить."
        return result.summary

    def should_route_to_inbox(self, result: StructuredAnalysisResult) -> bool:
        return result.should_go_to_inbox or result.primary_intent == IntentType.INBOX_REVIEW

