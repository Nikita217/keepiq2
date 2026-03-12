from __future__ import annotations

from domain.enums import IntentType, SourceType, SuggestionActionType
from domain.models import AnalysisContext, AnalysisItem, StructuredAnalysisResult, StructuredAnalysisSuggestion
from rules.base import DeterministicRule


TASK_HINTS = ("сделай", "сможешь", "можешь", "отправь", "пришли", "нужно", "надо")
REPLY_HINTS = ("ответь", "ответить", "reply", "не забудь ответить", "что ответить")
CHAT_HINTS = ("чат", "переписк", "сообщени", "диалог")


class ReplyLaterRule(DeterministicRule):
    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        text = (context.extracted.extracted_text or "").lower()
        chat_like = context.payload.source_type in {SourceType.SCREENSHOT, SourceType.FORWARDED_MESSAGE} or any(
            hint in text for hint in CHAT_HINTS
        )
        if not chat_like:
            return result
        if any(hint in text for hint in REPLY_HINTS):
            result.primary_intent = IntentType.REPLY_LATER
            result.items = [
                AnalysisItem(
                    type=IntentType.REPLY_LATER,
                    title=result.items[0].title if result.items else "Вернуться и ответить",
                    description=context.extracted.extracted_text,
                    needs_confirmation=False,
                    metadata={"source": "chat_context"},
                )
            ]
            result.user_action_suggestions = [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_REPLY_LATER,
                    label="Напомнить вечером",
                    target_item_index=0,
                    target_type=IntentType.REPLY_LATER,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.REVIEW_NOW,
                    label="Подготовить ответ",
                    target_item_index=0,
                    target_type=IntentType.REPLY_LATER,
                ),
            ]
            return result
        if any(hint in text for hint in TASK_HINTS):
            if result.items:
                result.items[0].type = IntentType.TASK
            else:
                result.items = [AnalysisItem(type=IntentType.TASK, title="Задача из переписки")]
            result.primary_intent = IntentType.TASK
        return result

