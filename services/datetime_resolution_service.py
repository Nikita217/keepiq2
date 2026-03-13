from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from dateparser.search import search_dates

from domain.analysis_models import AIAnalysisItem, AnalysisContext, ResolvedAnalysisItem
from rules.event_context_rules import apply_relative_offset
from rules.datetime_suggestion_rules import human_date_label
from utils.settings import get_settings

WEEKDAY_MAP = {
    "понедельник": 0,
    "вторник": 1,
    "среду": 2,
    "среда": 2,
    "четверг": 3,
    "пятницу": 4,
    "пятница": 4,
    "субботу": 5,
    "суббота": 5,
    "воскресенье": 6,
}
TIME_RE = re.compile(r"\b\d{1,2}[:.]\d{2}\b")


class DatetimeResolutionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def resolve_item(self, context: AnalysisContext, item: AIAnalysisItem, index: int) -> ResolvedAnalysisItem:
        text = context.extracted.extracted_text or context.payload.raw_text or ""
        resolved_datetime = item.datetime
        resolved_date = item.date_only
        event_datetime = item.event_date

        if item.relative_offset:
            source_event_dt = item.event_date
            if source_event_dt is None and item.date_only is not None:
                source_event_dt = datetime.combine(item.date_only, datetime.min.time()).replace(tzinfo=context.now.tzinfo)
            if source_event_dt is not None:
                shifted = apply_relative_offset(source_event_dt, item.relative_offset)
                if TIME_RE.search(text):
                    resolved_datetime = shifted
                    resolved_date = shifted.date()
                else:
                    resolved_datetime = None
                    resolved_date = shifted.date()
                    event_datetime = source_event_dt

        if resolved_datetime is not None and self._should_demote_to_date_only(resolved_datetime, text, context):
            resolved_date = resolved_datetime.date()
            resolved_datetime = None

        if resolved_datetime is None and resolved_date is None:
            resolved_datetime = self._extract_datetime(text, context.now)
            if resolved_datetime is not None and self._should_demote_to_date_only(resolved_datetime, text, context):
                resolved_date = resolved_datetime.date()
                resolved_datetime = None
            elif resolved_datetime is not None:
                resolved_date = resolved_datetime.date()
            else:
                resolved_date = self._extract_date(text, context.now)

        metadata = {}
        if resolved_date:
            metadata["date_label"] = human_date_label(resolved_date, today=context.now.date())
        if resolved_datetime:
            metadata["time_label"] = resolved_datetime.strftime("%H:%M")
        if event_datetime:
            metadata["event_date_label"] = human_date_label(event_datetime.date(), today=context.now.date())
        return ResolvedAnalysisItem(
            type=item.type,
            title=item.title,
            description=item.description,
            list_items=item.list_items,
            resolved_datetime=resolved_datetime,
            resolved_date=resolved_date,
            event_datetime=event_datetime,
            relative_offset=item.relative_offset,
            confidence=item.confidence,
            source_item_index=index,
            metadata=metadata,
        )

    def _should_demote_to_date_only(self, value: datetime, text: str, context: AnalysisContext) -> bool:
        if context.extracted and context.extracted.metadata.get("force_exact_time"):
            return False
        if not TIME_RE.search(text):
            return True
        if value.hour == 0 and value.minute == 0:
            return True
        return False

    def _extract_datetime(self, text: str, base_now: datetime) -> datetime | None:
        matches = search_dates(
            text,
            languages=["ru", "en"],
            settings={
                "TIMEZONE": self.settings.timezone,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        ) or []
        for phrase, parsed in matches:
            if TIME_RE.search(phrase):
                return parsed
        parsed_date = self._extract_date(text, base_now)
        explicit_time = TIME_RE.search(text)
        if parsed_date and explicit_time:
            hour_text, minute_text = explicit_time.group(0).replace('.', ':').split(':', 1)
            return datetime.combine(parsed_date, datetime.min.time().replace(hour=int(hour_text), minute=int(minute_text))).replace(tzinfo=base_now.tzinfo)
        return None

    def _extract_date(self, text: str, base_now: datetime) -> date | None:
        lowered = text.lower()
        if "сегодня" in lowered:
            return base_now.date()
        if "завтра" in lowered:
            return (base_now + timedelta(days=1)).date()
        if "послезавтра" in lowered:
            return (base_now + timedelta(days=2)).date()
        for weekday, index in WEEKDAY_MAP.items():
            if weekday in lowered:
                delta = (index - base_now.weekday()) % 7
                delta = 7 if delta == 0 else delta
                return (base_now + timedelta(days=delta)).date()
        matches = search_dates(
            text,
            languages=["ru", "en"],
            settings={
                "TIMEZONE": self.settings.timezone,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        ) or []
        for phrase, parsed in matches:
            lowered_phrase = phrase.lower()
            if re.search(r"\b\d{1,2}\s+[а-яa-z]+\b", lowered_phrase) or re.search(r"\b\d{1,2}[./-]\d{1,2}", lowered_phrase):
                return parsed.date()
        return None