from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dateparser.search import search_dates

from ai.base import AIProvider
from domain.enums import IntentType, SourceType, SuggestionActionType
from domain.models import (
    AnalysisContext,
    AnalysisItem,
    AnalysisTrace,
    ExtractedEntities,
    StructuredAnalysisResult,
    StructuredAnalysisSuggestion,
)
from utils.settings import get_settings
from utils.text import compact_text, split_lines_to_items


TASK_VERBS = ("купить", "написать", "позвонить", "отправить", "сделать", "проверить", "оплатить", "заказать")
IDEA_HINTS = ("идея", "idea", "мысль")
EVENT_HINTS = (
    "концерт",
    "самолет",
    "самолёт",
    "рейс",
    "поезд",
    "вылет",
    "регистрация",
    "бронь",
    "booking",
    "reservation",
    "встреча",
)
REPLY_HINTS = ("ответ", "reply", "что ответить", "ответить позже", "вернуться к сообщению")
REQUEST_HINTS = ("можешь", "сделай", "нужно", "надо", "пришли", "отправь")
CHAT_HINTS = ("чат", "перепис", "сообщени", "диалог")
REMINDER_HINTS = ("напомни", "напомнить", "не забудь")
RELATIVE_DATE_HINTS = (
    "сегодня",
    "завтра",
    "послезавтра",
    "в пятницу",
    "в субботу",
    "в воскресенье",
    "в понедельник",
    "в следующий",
    "на следующей неделе",
    "к выходным",
)
AMBIGUOUS_TIME_HINTS = ("утром", "днем", "днём", "вечером", "после обеда")
MONTHS = (
    "январ",
    "феврал",
    "март",
    "апрел",
    "мая",
    "июня",
    "июля",
    "август",
    "сентябр",
    "октябр",
    "ноябр",
    "декабр",
)


class HeuristicAIProvider(AIProvider):
    provider_name = "heuristic"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def analyze(self, context: AnalysisContext) -> StructuredAnalysisResult:
        text = compact_text(context.extracted.extracted_text)
        entities, exact_datetimes = self._extract_entities(text)
        if not text:
            return self._inbox_result(context, "Не удалось извлечь текст из объекта")
        if self._is_bad_transcription(context, text):
            return self._inbox_result(context, "Транскрипция получилась слишком слабой для уверенного разбора")
        if self._is_bad_ocr(context, text):
            return self._inbox_result(context, "В изображении не удалось уверенно прочитать текст")

        if context.payload.source_type == SourceType.VOICE_MESSAGE:
            voice_result = self._voice_result(context, text, entities, exact_datetimes)
            if voice_result is not None:
                return voice_result

        if self._is_shopping_list(text):
            items = self._shopping_items(text)
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary="Похоже, это список покупок",
                primary_intent=IntentType.LIST,
                confidence=0.94,
                items=[
                    AnalysisItem(
                        type=IntentType.LIST,
                        title="Список покупок",
                        description=text,
                        category="shopping",
                        list_items=items,
                        needs_confirmation=False,
                        metadata={"kind": "shopping"},
                    )
                ],
                extracted_entities=entities,
                user_action_suggestions=[
                    StructuredAnalysisSuggestion(
                        action=SuggestionActionType.CREATE_LIST,
                        label="Сохранить как список",
                        target_item_index=0,
                        target_type=IntentType.LIST,
                    )
                ],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Comma-separated shopping items are better represented as a list",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        if self._is_ticket_or_booking(context, text):
            title = self._extract_event_title(text) or "Событие из билета"
            item = AnalysisItem(
                type=IntentType.EVENT,
                title=title,
                description=text,
                datetime=exact_datetimes[0] if exact_datetimes else None,
                date_only=not self._has_explicit_time(text),
                category="travel" if "рейс" in text.lower() or "самолет" in text.lower() else "events",
                places=entities.places,
                links=entities.urls,
                needs_confirmation=not bool(exact_datetimes),
                uncertain_fields=[] if exact_datetimes else ["datetime"],
                metadata={
                    "ticket_like": True,
                    "date_value": exact_datetimes[0].isoformat() if exact_datetimes and not self._has_explicit_time(text) else None,
                },
            )
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary=f"Похоже, это билет или бронь: {title}",
                primary_intent=IntentType.EVENT,
                confidence=0.9,
                items=[item],
                extracted_entities=entities,
                user_action_suggestions=[],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Ticket or booking signal has event priority",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        if self._is_reply_later(context, text):
            return self._reminder_result(
                context,
                text,
                entities,
                exact_datetimes,
                summary="Нужно вернуться к сообщению позже",
                confidence=0.88,
                title=self._normalize_reminder_title(text, fallback="Ответить на сообщение"),
                metadata={"chat_like": True, "reply_like": True},
            )

        if self._is_chat_task(context, text):
            return self._reminder_result(
                context,
                text,
                entities,
                exact_datetimes,
                summary="В переписке есть просьба или поручение",
                confidence=0.83,
            )

        if self._is_idea(text):
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary="Похоже, это идея или заметка",
                primary_intent=IntentType.NOTE,
                confidence=0.88,
                items=[
                    AnalysisItem(
                        type=IntentType.NOTE,
                        title=self._title_from_text(text),
                        description=text,
                        category="ideas",
                        needs_confirmation=False,
                        metadata={"kind": "idea"},
                    )
                ],
                extracted_entities=entities,
                user_action_suggestions=[],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Idea hints detected",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        if self._is_event(text, entities):
            title = self._extract_event_title(text) or self._title_from_text(text, fallback="Событие")
            exact_datetime = exact_datetimes[0] if exact_datetimes and self._has_explicit_time(text) else None
            date_value = exact_datetimes[0].isoformat() if exact_datetimes else None
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary=f"Похоже, это событие: {title}",
                primary_intent=IntentType.EVENT,
                confidence=0.87,
                items=[
                    AnalysisItem(
                        type=IntentType.EVENT,
                        title=title,
                        description=text,
                        datetime=exact_datetime,
                        date_only=bool(date_value) and not self._has_explicit_time(text),
                        category="events",
                        places=entities.places,
                        links=entities.urls,
                        needs_confirmation=not self._has_explicit_time(text),
                        uncertain_fields=[] if self._has_explicit_time(text) else ["datetime"],
                        metadata={"date_value": date_value},
                    )
                ],
                extracted_entities=entities,
                user_action_suggestions=[],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Detected event keyword with date signal",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        if self._looks_like_reminder(text):
            return self._reminder_result(
                context,
                text,
                entities,
                exact_datetimes,
                summary="Похоже, это напоминание",
                confidence=0.89,
            )

        if self._is_link_note(context, text, entities):
            url = entities.urls[0] if entities.urls else context.payload.source_url
            host = urlparse(url).netloc if url else "ссылка"
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary=f"Похоже, это материал на потом: {host}",
                primary_intent=IntentType.NOTE,
                confidence=0.82,
                items=[
                    AnalysisItem(
                        type=IntentType.NOTE,
                        title=self._title_from_text(text, fallback=host or "Материал"),
                        description=text,
                        links=entities.urls,
                        needs_confirmation=False,
                        metadata={"url": url, "kind": "reference"},
                    )
                ],
                extracted_entities=entities,
                user_action_suggestions=[],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Link without explicit action",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        if context.payload.source_type in {SourceType.SCREENSHOT, SourceType.PHOTO, SourceType.IMAGE_WITH_TEXT, SourceType.MIXED_MESSAGE}:
            return StructuredAnalysisResult(
                source_type=context.payload.source_type,
                detected_language=self._detect_language(text),
                summary="Похоже, это заметка по материалу",
                primary_intent=IntentType.NOTE,
                confidence=0.86,
                items=[
                    AnalysisItem(
                        type=IntentType.NOTE,
                        title=self._title_from_text(text, fallback="Материал"),
                        description=text,
                        needs_confirmation=False,
                        metadata={"kind": "reference"},
                    )
                ],
                extracted_entities=entities,
                user_action_suggestions=[],
                should_store_original=True,
                should_go_to_inbox=False,
                reasoning_notes="Image content has no explicit action",
                trace=AnalysisTrace(provider=self.provider_name),
            )

        return StructuredAnalysisResult(
            source_type=context.payload.source_type,
            detected_language=self._detect_language(text),
            summary="Не удалось уверенно классифицировать объект",
            primary_intent=IntentType.INBOX_REVIEW,
            confidence=0.48,
            items=[],
            extracted_entities=entities,
            user_action_suggestions=[],
            should_store_original=True,
            should_go_to_inbox=True,
            reasoning_notes="Heuristics were not confident enough",
            trace=AnalysisTrace(provider=self.provider_name),
        )

    async def transcribe_audio(self, file_path: Path) -> str:
        return f"[transcription unavailable] {file_path.name}"

    async def extract_image_text(self, file_path: Path) -> str | None:
        return None

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        preview = compact_text(text)[:80]
        return {
            "short": "Увидел сообщение. Вернусь позже.",
            "polite": "Спасибо, увидел сообщение. Вернусь с ответом чуть позже.",
            "business": "Сообщение получил. Подготовлю ответ и вернусь позже.",
            "soft": f"Спасибо, я сохраню это и вернусь к ответу позже. {preview}".strip(),
        }

    def _reminder_result(
        self,
        context: AnalysisContext,
        text: str,
        entities: ExtractedEntities,
        exact_datetimes: list[datetime],
        *,
        summary: str,
        confidence: float,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> StructuredAnalysisResult:
        exact_datetime = exact_datetimes[0] if exact_datetimes and self._has_explicit_time(text) else None
        date_value = exact_datetimes[0].isoformat() if exact_datetimes else None
        item = AnalysisItem(
            type=IntentType.REMINDER,
            title=title or self._normalize_reminder_title(text),
            description=text,
            datetime=exact_datetime,
            date_only=bool(date_value) and not self._has_explicit_time(text) or bool(entities.ambiguous_datetimes),
            category="shopping" if text.lower().startswith("купить ") else None,
            people=entities.people,
            links=entities.urls,
            needs_confirmation=bool(entities.ambiguous_datetimes) or (bool(date_value) and not self._has_explicit_time(text)),
            uncertain_fields=["datetime"] if bool(entities.ambiguous_datetimes) or (bool(date_value) and not self._has_explicit_time(text)) else [],
            metadata={"date_value": date_value, **(metadata or {})},
        )
        return StructuredAnalysisResult(
            source_type=context.payload.source_type,
            detected_language=self._detect_language(text),
            summary=summary,
            primary_intent=IntentType.REMINDER,
            confidence=confidence,
            items=[item],
            extracted_entities=entities,
            user_action_suggestions=[],
            should_store_original=True,
            should_go_to_inbox=False,
            reasoning_notes="Explicit reminder or action signal detected",
            trace=AnalysisTrace(provider=self.provider_name),
        )

    def _voice_result(
        self,
        context: AnalysisContext,
        text: str,
        entities: ExtractedEntities,
        exact_datetimes: list[datetime],
    ) -> StructuredAnalysisResult | None:
        segments = [compact_text(chunk) for chunk in re.split(r"[,;]| и еще | и ещё | потом |\n", text) if compact_text(chunk)]
        if len(segments) < 2:
            return None
        items: list[AnalysisItem] = []
        for segment in segments:
            if self._is_idea(segment):
                items.append(
                    AnalysisItem(
                        type=IntentType.NOTE,
                        title=self._title_from_text(segment),
                        description=segment,
                        category="ideas",
                        needs_confirmation=False,
                    )
                )
            elif self._looks_like_list_segment(segment):
                items.append(
                    AnalysisItem(
                        type=IntentType.LIST,
                        title=self._title_from_text(segment, fallback="Список"),
                        description=segment,
                        list_items=split_lines_to_items(segment),
                        needs_confirmation=False,
                    )
                )
            else:
                items.append(
                    AnalysisItem(
                        type=IntentType.REMINDER,
                        title=self._normalize_reminder_title(segment),
                        description=segment,
                        datetime=exact_datetimes[0] if exact_datetimes and self._has_explicit_time(segment) else None,
                        date_only=bool(entities.ambiguous_datetimes) and not self._has_explicit_time(segment),
                        needs_confirmation=bool(entities.ambiguous_datetimes),
                        uncertain_fields=["datetime"] if entities.ambiguous_datetimes else [],
                    )
                )
        note_count = sum(1 for item in items if item.type == IntentType.NOTE)
        reminder_count = sum(1 for item in items if item.type == IntentType.REMINDER)
        list_count = sum(1 for item in items if item.type == IntentType.LIST)
        parts: list[str] = []
        if reminder_count:
            parts.append(f"{reminder_count} напоминания")
        if list_count:
            parts.append(f"{list_count} списка")
        if note_count:
            parts.append(f"{note_count} заметки")
        summary = "В голосовом несколько пунктов"
        if parts:
            summary = f"В голосовом: {', '.join(parts)}"
        return StructuredAnalysisResult(
            source_type=context.payload.source_type,
            detected_language=self._detect_language(text),
            summary=summary,
            primary_intent=items[0].type if items else IntentType.INBOX_REVIEW,
            confidence=0.87,
            items=items,
            extracted_entities=entities,
            user_action_suggestions=[
                StructuredAnalysisSuggestion(action=SuggestionActionType.SAVE_ALL, label="Сохранить все"),
                StructuredAnalysisSuggestion(action=SuggestionActionType.REVIEW_NOW, label="Проверить"),
            ],
            should_store_original=True,
            should_go_to_inbox=False,
            reasoning_notes="Voice transcript contains several semantic segments",
            trace=AnalysisTrace(provider=self.provider_name),
        )

    def _extract_entities(self, text: str) -> tuple[ExtractedEntities, list[datetime]]:
        entities = ExtractedEntities()
        if not text:
            return entities, []

        for token in text.split():
            if token.startswith("http://") or token.startswith("https://"):
                entities.urls.append(token.rstrip(".,)"))

        time_matches = re.findall(r"\b(\d{1,2}[:.]\d{2})\b", text)
        entities.times.extend(match.replace(".", ":") for match in time_matches)

        date_matches = search_dates(
            text,
            languages=["ru", "en"],
            settings={
                "TIMEZONE": self.settings.timezone,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        ) or []
        exact_datetimes: list[datetime] = []
        for phrase, parsed in date_matches:
            normalized_phrase = compact_text(phrase.lower())
            if self._is_ambiguous_datetime_phrase(normalized_phrase):
                entities.ambiguous_datetimes.append(phrase)
                continue
            exact_datetimes.append(parsed)
            entities.dates.append(parsed.date().isoformat())
            if self._has_explicit_time(phrase):
                entities.times.append(parsed.strftime("%H:%M"))

        if entities.times and not self._contains_date_hint(text):
            exact_datetimes = []
            entities.dates = []
            entities.ambiguous_datetimes.extend(entities.times)
        elif entities.times and not entities.dates:
            entities.ambiguous_datetimes.extend(entities.times)

        people = re.findall(r"\b[А-ЯЁ][а-яё]{2,}\b", text)
        entities.people.extend(name for name in people if name not in {"Идея"})
        return entities, exact_datetimes

    def _contains_date_hint(self, text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in RELATIVE_DATE_HINTS) or any(month in lowered for month in MONTHS) or bool(
            re.search(r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b", lowered)
        )

    def _is_ambiguous_datetime_phrase(self, phrase: str) -> bool:
        if any(hint in phrase for hint in RELATIVE_DATE_HINTS):
            return True
        if any(hint in phrase for hint in AMBIGUOUS_TIME_HINTS):
            return True
        if re.fullmatch(r"(в )?\d{1,2}:\d{2}", phrase):
            return True
        if self._has_explicit_time(phrase) and not any(hint in phrase for hint in RELATIVE_DATE_HINTS) and not any(
            month in phrase for month in MONTHS
        ) and not re.search(r"\b\d{1,2}[./-]\d{1,2}\b", phrase):
            return True
        return False

    def _has_explicit_time(self, text: str) -> bool:
        return bool(re.search(r"\b\d{1,2}[:.]\d{2}\b", text))

    def _is_shopping_list(self, text: str) -> bool:
        lowered = text.lower()
        return lowered.startswith("купить ") and len(self._shopping_items(text)) >= 2

    def _shopping_items(self, text: str) -> list[str]:
        lowered = text.lower()
        tail = text[len("купить ") :] if lowered.startswith("купить ") else text
        return [item for item in split_lines_to_items(tail) if item]

    def _is_ticket_or_booking(self, context: AnalysisContext, text: str) -> bool:
        if context.payload.source_type in {SourceType.TICKET, SourceType.BOOKING_CONFIRMATION}:
            return True
        return context.extracted.metadata.get("document_hint") == "ticket_or_booking" or any(
            hint in text.lower() for hint in EVENT_HINTS
        ) and context.payload.source_type in {SourceType.DOCUMENT, SourceType.IMAGE_WITH_TEXT}

    def _is_reply_later(self, context: AnalysisContext, text: str) -> bool:
        lowered = text.lower()
        chat_like = context.payload.source_type in {SourceType.SCREENSHOT, SourceType.FORWARDED_MESSAGE} or any(
            hint in lowered for hint in CHAT_HINTS
        )
        return chat_like and any(hint in lowered for hint in REPLY_HINTS)

    def _is_chat_task(self, context: AnalysisContext, text: str) -> bool:
        lowered = text.lower()
        chat_like = context.payload.source_type in {SourceType.SCREENSHOT, SourceType.FORWARDED_MESSAGE, SourceType.MIXED_MESSAGE} or any(
            hint in lowered for hint in CHAT_HINTS
        )
        return chat_like and any(hint in lowered for hint in REQUEST_HINTS)

    def _is_idea(self, text: str) -> bool:
        lowered = text.lower()
        return lowered.startswith(IDEA_HINTS) or any(hint in lowered for hint in IDEA_HINTS)

    def _is_event(self, text: str, entities: ExtractedEntities) -> bool:
        lowered = text.lower()
        return bool(entities.dates) and any(hint in lowered for hint in EVENT_HINTS)

    def _looks_like_reminder(self, text: str) -> bool:
        lowered = text.lower()
        return (
            lowered.startswith(TASK_VERBS)
            or lowered.startswith(REMINDER_HINTS)
            or any(f" {verb} " in f" {lowered} " for verb in TASK_VERBS)
            or any(hint in lowered for hint in REMINDER_HINTS)
        )

    def _is_link_note(self, context: AnalysisContext, text: str, entities: ExtractedEntities) -> bool:
        if context.payload.source_type == SourceType.LINK and not self._looks_like_reminder(text):
            return True
        return bool(entities.urls) and not self._looks_like_reminder(text) and not self._is_event(text, entities)

    def _normalize_reminder_title(self, text: str, fallback: str = "Напоминание") -> str:
        cleaned = compact_text(text)
        lowered = cleaned.lower()
        prefixes = ("завтра ", "послезавтра ", "сегодня ", "напомни ", "напомнить ", "не забудь ")
        for prefix in prefixes:
            if lowered.startswith(prefix):
                cleaned = compact_text(cleaned[len(prefix) :])
                lowered = cleaned.lower()
        if cleaned.lower().startswith("ответить "):
            return cleaned[:120]
        return cleaned[:120] or fallback

    def _extract_event_title(self, text: str) -> str | None:
        if "концерт" in text.lower():
            return compact_text(text)
        for keyword in EVENT_HINTS:
            if keyword in text.lower():
                return compact_text(text)
        return None

    def _detect_language(self, text: str) -> str | None:
        if not text:
            return None
        return "ru" if re.search(r"[А-Яа-яЁё]", text) else "en"

    def _title_from_text(self, text: str, fallback: str = "Сохраненный объект") -> str:
        return compact_text(text)[:120] or fallback

    def _looks_like_list_segment(self, text: str) -> bool:
        return len(split_lines_to_items(text)) >= 2 and "," in text

    def _is_bad_transcription(self, context: AnalysisContext, text: str) -> bool:
        return context.payload.source_type == SourceType.VOICE_MESSAGE and text.startswith("[transcription unavailable]")

    def _is_bad_ocr(self, context: AnalysisContext, text: str) -> bool:
        return context.payload.source_type in {SourceType.SCREENSHOT, SourceType.IMAGE_WITH_TEXT, SourceType.PHOTO} and not text

    def _inbox_result(self, context: AnalysisContext, summary: str) -> StructuredAnalysisResult:
        return StructuredAnalysisResult(
            source_type=context.payload.source_type,
            detected_language=None,
            summary=summary,
            primary_intent=IntentType.INBOX_REVIEW,
            confidence=0.25,
            items=[],
            extracted_entities=ExtractedEntities(),
            user_action_suggestions=[],
            should_store_original=True,
            should_go_to_inbox=True,
            reasoning_notes=summary,
            trace=AnalysisTrace(provider=self.provider_name, fallback_used=True),
        )

