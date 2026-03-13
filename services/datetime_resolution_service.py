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


class DatetimeResolutionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def resolve_item(self, context: AnalysisContext, item: AIAnalysisItem, index: int) -> ResolvedAnalysisItem:
        resolved_datetime = item.datetime
        resolved_date = item.date_only
        event_datetime = item.event_date

        if item.relative_offset and item.event_date:
            shifted = apply_relative_offset(item.event_date, item.relative_offset)
            if item.event_date.hour or item.event_date.minute:
                resolved_datetime = shifted
                resolved_date = shifted.date()
            else:
                resolved_date = shifted.date()

        if resolved_datetime is None and resolved_date is None:
            resolved_datetime = self._extract_datetime(context.extracted.extracted_text or context.payload.raw_text or "", context.now)
            if resolved_datetime is not None:
                resolved_date = resolved_datetime.date()
            else:
                resolved_date = self._extract_date(context.extracted.extracted_text or context.payload.raw_text or "", context.now)

        metadata = {}
        if resolved_date:
            metadata["date_label"] = human_date_label(resolved_date, today=context.now.date())
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
            if re.search(r"\b\d{1,2}[:.]\d{2}\b", phrase):
                return parsed
        parsed_date = self._extract_date(text, base_now)
        explicit_time = re.search(r"\b(?P<hour>\d{1,2})[:.](?P<minute>\d{2})\b", text)
        if parsed_date and explicit_time:
            hour = int(explicit_time.group("hour"))
            minute = int(explicit_time.group("minute"))
            return datetime.combine(parsed_date, datetime.min.time().replace(hour=hour, minute=minute)).replace(tzinfo=base_now.tzinfo)
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
