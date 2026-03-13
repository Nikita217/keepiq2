from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from dateparser.search import search_dates

from ai.base import AIProvider
from domain.analysis_models import AIAnalysisItem, AIAnalysisResult, AnalysisContext, ExtractedEntities, ReasoningFlags
from domain.enums import FinalType, SourceType
from rules.event_context_rules import detect_event_context
from rules.list_rules import detect_list_items, looks_like_list
from rules.motivation_filter_rules import strip_background_motivation
from utils.settings import get_settings
from utils.text import compact_text

TASK_VERBS = ("купить", "написать", "позвонить", "отправить", "сделать", "записаться", "заказать", "оплатить")
EVENT_HINTS = ("концерт", "встреча", "поездка", "бронь", "booking", "reservation", "прием", "приём", "билет")
IDEA_HINTS = ("идея", "мысль", "idea")
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


class HeuristicAIProvider(AIProvider):
    provider_name = "heuristic"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def analyze(self, context: AnalysisContext) -> AIAnalysisResult:
        text = compact_text(context.extracted.extracted_text or context.payload.raw_text)
        entities = self._extract_entities(text, context)
        cleaned_text, has_motivation = strip_background_motivation(text)
        flags = ReasoningFlags(
            contains_background_motivation=has_motivation,
            contains_actionable_request=self._contains_actionable_request(cleaned_text),
            contains_event_context=False,
            contains_multiple_independent_actions=False,
            contains_list_pattern=False,
            ambiguous_datetime=False,
        )

        if context.extracted.extraction_errors and not text:
            return self._fallback_result(context, text, "Не удалось извлечь содержимое", entities, 0.2)

        if context.payload.source_type == SourceType.VOICE_MESSAGE and text.startswith("[transcription unavailable]"):
            return self._fallback_result(context, text, "Не удалось уверенно расшифровать голосовое", entities, 0.2)

        if context.payload.source_type in {SourceType.PHOTO, SourceType.SCREENSHOT, SourceType.IMAGE_WITH_TEXT} and not text:
            return self._fallback_result(context, text, "Не удалось уверенно прочитать изображение", entities, 0.2)

        if looks_like_list(cleaned_text):
            flags.contains_list_pattern = True
            items = detect_list_items(cleaned_text)
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Список",
                primary_type=FinalType.LIST,
                secondary_candidate_type=FinalType.NOTE,
                confidence=0.94,
                needs_user_confirmation=False,
                items=[
                    AIAnalysisItem(
                        type=FinalType.LIST,
                        title=self._guess_list_title(cleaned_text),
                        description=None,
                        list_items=items,
                        confidence=0.94,
                    )
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        event_context = detect_event_context(cleaned_text)
        if event_context is not None:
            flags.contains_event_context = True
            flags.ambiguous_datetime = event_context["event_date"] is None
            confidence = 0.92 if event_context["event_date"] else 0.58
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Напоминание относительно события",
                primary_type=FinalType.REMINDER,
                secondary_candidate_type=FinalType.EVENT,
                confidence=confidence,
                needs_user_confirmation=event_context["event_date"] is None,
                items=[
                    AIAnalysisItem(
                        type=FinalType.REMINDER,
                        title=event_context["title"],
                        description=None,
                        event_date=event_context["event_date"],
                        relative_offset=event_context["relative_offset"],
                        confidence=confidence,
                    )
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        if self._looks_like_multiple_actions(cleaned_text):
            shared_date = self._parse_relative_date(cleaned_text, context.now)
            flags.contains_multiple_independent_actions = True
            flags.ambiguous_datetime = shared_date is not None and self._extract_time(cleaned_text) is None
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Несколько действий",
                primary_type=FinalType.REMINDER,
                secondary_candidate_type=None,
                confidence=0.84,
                needs_user_confirmation=True,
                items=[
                    AIAnalysisItem(
                        type=FinalType.REMINDER,
                        title=self._normalize_action_title(part),
                        description=None,
                        date_only=shared_date,
                        confidence=0.84,
                    )
                    for part in self._split_actions(cleaned_text)
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        if self._looks_like_explicit_reminder(cleaned_text):
            explicit_datetime = self._extract_explicit_datetime(cleaned_text, context.now)
            explicit_date = self._parse_relative_date(cleaned_text, context.now)
            confidence = 0.9 if explicit_datetime or explicit_date else 0.56
            flags.ambiguous_datetime = explicit_datetime is None and explicit_date is not None
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Напоминание",
                primary_type=FinalType.REMINDER,
                secondary_candidate_type=FinalType.NOTE if explicit_datetime is None and explicit_date is None else None,
                confidence=confidence,
                needs_user_confirmation=explicit_datetime is None,
                items=[
                    AIAnalysisItem(
                        type=FinalType.REMINDER,
                        title=self._normalize_action_title(cleaned_text),
                        description=None,
                        datetime=explicit_datetime,
                        date_only=None if explicit_datetime else explicit_date,
                        confidence=confidence,
                    )
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        if self._looks_like_event(cleaned_text, context):
            explicit_datetime = self._extract_explicit_datetime(cleaned_text, context.now)
            explicit_date = self._parse_relative_date(cleaned_text, context.now)
            confidence = 0.9 if explicit_datetime or explicit_date else 0.62
            flags.ambiguous_datetime = explicit_datetime is None
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Событие",
                primary_type=FinalType.EVENT,
                secondary_candidate_type=FinalType.NOTE,
                confidence=confidence,
                needs_user_confirmation=explicit_datetime is None and explicit_date is None,
                items=[
                    AIAnalysisItem(
                        type=FinalType.EVENT,
                        title=self._normalize_event_title(cleaned_text),
                        description=None,
                        datetime=explicit_datetime,
                        date_only=None if explicit_datetime else explicit_date,
                        confidence=confidence,
                    )
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        if self._looks_like_note(cleaned_text, context):
            return AIAnalysisResult(
                source_type=context.payload.source_type,
                normalized_text=text,
                summary="Заметка",
                primary_type=FinalType.NOTE,
                secondary_candidate_type=FinalType.LIST if len(detect_list_items(cleaned_text)) > 1 else None,
                confidence=0.88,
                needs_user_confirmation=False,
                items=[
                    AIAnalysisItem(
                        type=FinalType.NOTE,
                        title=self._normalize_note_title(cleaned_text),
                        description=text or None,
                        confidence=0.88,
                    )
                ],
                extracted_entities=entities,
                reasoning_flags=flags,
            )

        return self._fallback_result(context, text, "Лучше оставить во входящих или сохранить заметкой", entities, 0.35)

    async def transcribe_audio(self, file_path: Path) -> str:
        return f"[transcription unavailable] {file_path.name}"

    async def extract_image_text(self, file_path: Path) -> str | None:
        return None

    def _fallback_result(
        self,
        context: AnalysisContext,
        normalized_text: str,
        summary: str,
        entities: ExtractedEntities,
        confidence: float,
    ) -> AIAnalysisResult:
        items = []
        if confidence >= 0.4:
            items.append(
                AIAnalysisItem(
                    type=FinalType.NOTE,
                    title=self._normalize_note_title(normalized_text or "Материал"),
                    description=normalized_text or None,
                    confidence=confidence,
                )
            )
        return AIAnalysisResult(
            source_type=context.payload.source_type,
            normalized_text=normalized_text,
            summary=summary,
            primary_type=FinalType.NOTE,
            secondary_candidate_type=None,
            confidence=confidence,
            needs_user_confirmation=True,
            items=items,
            extracted_entities=entities,
            reasoning_flags=ReasoningFlags(),
        )

    def _extract_entities(self, text: str, context: AnalysisContext) -> ExtractedEntities:
        entities = ExtractedEntities()
        if not text:
            return entities
        entities.urls.extend(match.rstrip(".,)") for match in re.findall(r"https?://\S+", text))
        if parsed_date := self._parse_relative_date(text, context.now):
            entities.dates.append(parsed_date.isoformat())
        if explicit_datetime := self._extract_explicit_datetime(text, context.now):
            entities.dates = [explicit_datetime.date().isoformat()]
            entities.times = [explicit_datetime.strftime("%H:%M")]
        elif explicit_time := self._extract_time(text):
            entities.times = [explicit_time.strftime("%H:%M")]
        if "the hatters" in text.lower():
            entities.titles.append("The Hatters")
        return entities

    def _contains_actionable_request(self, text: str) -> bool:
        lowered = text.lower()
        return "напом" in lowered or any(verb in lowered for verb in TASK_VERBS)

    def _looks_like_explicit_reminder(self, text: str) -> bool:
        lowered = text.lower()
        return "напом" in lowered or lowered.startswith(TASK_VERBS) or any(f" {verb} " in f" {lowered} " for verb in TASK_VERBS)

    def _looks_like_multiple_actions(self, text: str) -> bool:
        lowered = text.lower()
        return " и " in lowered and sum(1 for verb in TASK_VERBS if verb in lowered) >= 2

    def _split_actions(self, text: str) -> list[str]:
        normalized = re.sub(r"^(сегодня|завтра|послезавтра)\s+", "", text.strip(), flags=re.IGNORECASE)
        return [compact_text(part) for part in re.split(r"\s+и\s+", normalized) if compact_text(part)]

    def _looks_like_event(self, text: str, context: AnalysisContext) -> bool:
        lowered = text.lower()
        if context.payload.source_type in {SourceType.TICKET, SourceType.BOOKING_CONFIRMATION}:
            return True
        return any(hint in lowered for hint in EVENT_HINTS) and (
            self._parse_relative_date(text, context.now) is not None or self._extract_explicit_datetime(text, context.now) is not None
        )

    def _looks_like_note(self, text: str, context: AnalysisContext) -> bool:
        lowered = text.lower()
        if any(lowered.startswith(prefix) for prefix in IDEA_HINTS):
            return True
        return context.payload.source_type in {
            SourceType.SCREENSHOT,
            SourceType.PHOTO,
            SourceType.IMAGE_WITH_TEXT,
            SourceType.DOCUMENT,
            SourceType.LINK,
            SourceType.FORWARDED_MESSAGE,
            SourceType.MIXED_MESSAGE,
        }

    def _extract_explicit_datetime(self, text: str, base_now: datetime) -> datetime | None:
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
        parsed_date = self._parse_relative_date(text, base_now)
        parsed_time = self._extract_time(text)
        if parsed_date and parsed_time:
            return datetime.combine(parsed_date, parsed_time.timetz()).replace(tzinfo=base_now.tzinfo)
        return None

    def _parse_relative_date(self, text: str, base_now: datetime) -> date | None:
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

    def _extract_time(self, text: str) -> datetime | None:
        match = re.search(r"\b(?P<hour>\d{1,2})[:.](?P<minute>\d{2})\b", text)
        if not match:
            return None
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _normalize_action_title(self, text: str) -> str:
        cleaned = compact_text(text)
        cleaned = re.sub(r"^(напомни( мне)?\s+)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(сегодня|завтра|послезавтра)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(поэтому)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = compact_text(cleaned)
        return cleaned[:160] or "Напоминание"

    def _normalize_event_title(self, text: str) -> str:
        cleaned = compact_text(text)
        cleaned = re.sub(r"^\d{1,2}\s+[а-яa-z]+\s+", "", cleaned, flags=re.IGNORECASE)
        return cleaned[:160] or "Событие"

    def _normalize_note_title(self, text: str) -> str:
        cleaned = compact_text(text)
        cleaned = re.sub(r"^(идея|мысль)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned[:160] or "Заметка"

    def _guess_list_title(self, text: str) -> str:
        lowered = text.lower()
        if lowered.startswith("купить "):
            return "Список покупок"
        return "Список"
