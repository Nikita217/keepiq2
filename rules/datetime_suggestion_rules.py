from __future__ import annotations

from datetime import timedelta

from domain.enums import IntentType, SuggestionActionType
from domain.models import AnalysisContext, StructuredAnalysisResult, StructuredAnalysisSuggestion
from rules.base import DeterministicRule
from utils.settings import get_settings


class DateTimeSuggestionRule(DeterministicRule):
    def __init__(self) -> None:
        self.settings = get_settings()

    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        if result.should_go_to_inbox:
            return result
        suggestions = list(result.user_action_suggestions)
        if not result.items:
            result.user_action_suggestions = suggestions
            return result

        primary = result.items[0]
        if primary.type == IntentType.REMINDER and self._has_relative_day(result):
            base_day = self._base_day(context)
            for hour in self.settings.ai_task_suggestion_hours[:3]:
                suggestions.append(
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label=f"Завтра в {hour:02d}:00",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=base_day.replace(hour=hour, minute=0, second=0, microsecond=0),
                    )
                )
            suggestions.append(
                StructuredAnalysisSuggestion(
                    action=SuggestionActionType.CREATE_REMINDER,
                    label="Просто сохранить",
                    target_item_index=0,
                    target_type=IntentType.REMINDER,
                )
            )
        elif primary.type == IntentType.REMINDER and primary.datetime and not primary.date_only:
            suggestions.extend(
                [
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="Оставить как есть",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime,
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="На час раньше",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime - timedelta(hours=1),
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_REMINDER,
                        label="На час позже",
                        target_item_index=0,
                        target_type=IntentType.REMINDER,
                        scheduled_for=primary.datetime + timedelta(hours=1),
                    ),
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_NOTE,
                        label="Сохранить заметкой",
                        target_item_index=0,
                        target_type=IntentType.NOTE,
                    ),
                ]
            )
        elif primary.type == IntentType.EVENT and primary.date_only:
            event_day = primary.datetime or self._date_only_from_metadata(primary.metadata)
            if event_day is not None:
                event_day = event_day.replace(hour=9, minute=0, second=0, microsecond=0)
                suggestions.extend(
                    [
                        StructuredAnalysisSuggestion(
                            action=SuggestionActionType.CREATE_REMINDER,
                            label="Утром в этот день",
                            target_item_index=0,
                            target_type=IntentType.REMINDER,
                            scheduled_for=event_day,
                        ),
                        StructuredAnalysisSuggestion(
                            action=SuggestionActionType.CREATE_REMINDER,
                            label="Днем",
                            target_item_index=0,
                            target_type=IntentType.REMINDER,
                            scheduled_for=event_day.replace(hour=14),
                        ),
                        StructuredAnalysisSuggestion(
                            action=SuggestionActionType.CREATE_REMINDER,
                            label="Вечером",
                            target_item_index=0,
                            target_type=IntentType.REMINDER,
                            scheduled_for=event_day.replace(hour=19),
                        ),
                        StructuredAnalysisSuggestion(
                            action=SuggestionActionType.CREATE_REMINDER,
                            label="За день до этого",
                            target_item_index=0,
                            target_type=IntentType.REMINDER,
                            scheduled_for=event_day - timedelta(days=1),
                        ),
                    ]
                )
        result.user_action_suggestions = self._dedupe(suggestions)
        return result

    def _has_relative_day(self, result: StructuredAnalysisResult) -> bool:
        return bool(result.extracted_entities.ambiguous_datetimes) or any(
            item.date_only and item.datetime is None for item in result.items
        )

    def _base_day(self, context: AnalysisContext):
        return (context.now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    def _date_only_from_metadata(self, metadata: dict):
        value = metadata.get("date_value")
        if not value:
            return None
        try:
            from datetime import datetime

            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _dedupe(self, suggestions: list[StructuredAnalysisSuggestion]) -> list[StructuredAnalysisSuggestion]:
        seen: set[tuple[str, str, str | None]] = set()
        unique: list[StructuredAnalysisSuggestion] = []
        for suggestion in suggestions:
            key = (
                suggestion.action.value,
                suggestion.label,
                suggestion.scheduled_for.isoformat() if suggestion.scheduled_for else None,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(suggestion)
        return unique[:4]

