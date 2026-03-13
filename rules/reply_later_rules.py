from __future__ import annotations

from datetime import timedelta

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
            reminder_at = (context.now + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
            result.primary_intent = IntentType.REMINDER
            result.items = [
                AnalysisItem(
                    type=IntentType.REMINDER,
                    title=result.items[0].title if result.items else "Ответить на сообщение",
                    description=context.extracted.extracted_text,
                    needs_confirmation=False,
                    metadata={"source": "chat_context", "reply_like": True},
                )
            ]
            result.user_action_suggestions = [
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_REMINDER,
                    label="Напомнить вечером",
                    target_item_index=0,
                    target_type=IntentType.REMINDER,
                    scheduled_for=reminder_at,
                ),
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_NOTE,
                    label="Сохранить заметкой",
                    target_item_index=0,
                    target_type=IntentType.NOTE,
                ),
            ]
            return result
        if any(hint in text for hint in TASK_HINTS):
            if result.items:
                result.items[0].type = IntentType.REMINDER
            else:
                result.items = [AnalysisItem(type=IntentType.REMINDER, title="Напоминание из переписки")]
            result.primary_intent = IntentType.REMINDER
        return result

