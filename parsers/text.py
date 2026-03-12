from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import urlparse

from parsers.dates import extract_dates
from parsers.tickets import looks_like_ticket
from schemas.ai import AnalysisPayload, CandidateObject, ExtractedEntity
from utils.text import compact_text, split_lines_to_items


TASK_VERBS = ["купить", "отправить", "написать", "позвонить", "сделать", "оплатить", "заказать", "проверить"]
REPLY_HINTS = ["ответить", "reply", "перепис", "сообщени", "чат", "вернуться"]
IDEA_HINTS = ["идея", "мысль", "референс", "сохранить", "заметка"]
QUESTION_WORDS = [
    "что",
    "как",
    "когда",
    "где",
    "почему",
    "зачем",
    "кто",
    "сколько",
    "какой",
    "какая",
    "какие",
    "можно ли",
    "нужно ли",
]
CHAT_HINTS = ["переписка", "чат", "сообщение", "message", "telegram", "whatsapp"]


class HeuristicTextParser:
    def analyze(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        context = self._parse_context(text)
        normalized = context["semantic_text"]
        lowered = normalized.lower()
        dates = extract_dates(normalized)
        entities: list[ExtractedEntity] = []
        candidates: list[CandidateObject] = []
        proposed_type = "saved"
        summary = normalized[:180] if normalized else "Пустой ввод"
        confidence = 0.45
        needs_confirmation = True
        assistant_response: str | None = None
        clarification_question: str | None = None

        urls = [token for token in normalized.split() if token.startswith("http://") or token.startswith("https://")]
        for url in urls:
            parsed = urlparse(url)
            entities.append(
                ExtractedEntity(entity_type="url", value=url, normalized_value=parsed.netloc, confidence=0.95)
            )

        for dt in dates:
            entities.append(
                ExtractedEntity(
                    entity_type="datetime",
                    value=dt.isoformat(),
                    normalized_value=dt.isoformat(),
                    confidence=0.74,
                )
            )

        voice_candidates = self._voice_candidates(normalized, dates, hint)
        shopping_items = self._shopping_items(normalized, lowered)

        if self._looks_like_question(normalized, lowered, hint):
            proposed_type = "answer"
            confidence = 0.82
            needs_confirmation = False
            assistant_response = self._build_question_answer(normalized, hint)
            summary = "Распознал вопрос и подготовил ответ"
            candidates.append(
                CandidateObject(
                    object_type="note",
                    title=normalized[:80] or "Вопрос",
                    description=normalized,
                    metadata={"kind": "answer_context"},
                )
            )
        elif voice_candidates:
            proposed_type = "task"
            confidence = 0.86
            needs_confirmation = False
            candidates = voice_candidates
            summary = f"Выделил {len(voice_candidates)} пункта из одного сообщения"
            if dates:
                clarification_question = "Поставить напоминание к указанному времени?"
        elif looks_like_ticket(normalized) or hint in {"ticket", "booking"}:
            proposed_type = "event"
            confidence = 0.84
            needs_confirmation = False if dates else True
            candidates.append(
                CandidateObject(
                    object_type="event",
                    title="Событие из билета" if len(normalized) > 60 else normalized,
                    description=normalized,
                    event_at=dates[0] if dates else None,
                    metadata={"kind": "ticket_or_booking", "source_hint": context["filename"]},
                )
            )
            if dates:
                candidates.append(
                    CandidateObject(
                        object_type="reminder",
                        title="Напоминание о событии",
                        remind_at=dates[0] - timedelta(hours=3),
                        description="Автопредложение напоминания за 3 часа",
                        metadata={"linked_to": "event"},
                    )
                )
        elif self._looks_like_chat_capture(lowered, context) or any(word in lowered for word in REPLY_HINTS) or hint == "forwarded":
            proposed_type = "reply_later"
            confidence = 0.82
            needs_confirmation = False if hint == "forwarded" else True
            candidates.append(
                CandidateObject(
                    object_type="reply_later",
                    title=normalized[:80] or "Вернуться к сообщению",
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
        elif lowered.startswith("напомни") or "не забыть" in lowered or "напомнить" in lowered:
            proposed_type = "reminder"
            confidence = 0.87 if dates else 0.72
            needs_confirmation = not bool(dates)
            title = normalized.replace("напомни", "").replace("напомнить", "").strip(" :.-")
            candidates.append(
                CandidateObject(
                    object_type="task",
                    title=title or "Напоминание",
                    description=normalized,
                    due_at=dates[0] if dates else None,
                    metadata={"linked_to": "reminder"},
                )
            )
            candidates.append(
                CandidateObject(
                    object_type="reminder",
                    title=title or "Напоминание",
                    remind_at=dates[0] if dates else None,
                    description=normalized,
                    metadata={"linked_to": "task"},
                )
            )
        elif shopping_items:
            proposed_type = "list"
            confidence = 0.84
            needs_confirmation = False
            candidates.append(
                CandidateObject(
                    object_type="list",
                    title="Список покупок",
                    description=normalized,
                    items=shopping_items,
                    metadata={"kind": "shopping"},
                )
            )
        elif len(split_lines_to_items(normalized)) >= 3 and any(verb in lowered for verb in TASK_VERBS):
            proposed_type = "list"
            confidence = 0.8
            needs_confirmation = False
            items = split_lines_to_items(normalized)
            candidates.append(
                CandidateObject(
                    object_type="list",
                    title="Список покупок" if "купить" in lowered else "Список",
                    description=normalized,
                    items=items,
                )
            )
        elif any(marker in lowered for marker in IDEA_HINTS):
            proposed_type = "note"
            confidence = 0.72
            candidates.append(CandidateObject(object_type="note", title=normalized[:80], description=normalized))
        elif self._looks_like_explicit_task(lowered):
            proposed_type = "task"
            confidence = 0.82
            needs_confirmation = False
            candidates.append(
                CandidateObject(
                    object_type="task",
                    title=normalized[:100],
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
            if dates:
                clarification_question = "Поставить отдельное напоминание к этому сроку?"
        elif urls:
            proposed_type = "saved"
            confidence = 0.73
            candidates.append(
                CandidateObject(
                    object_type="saved",
                    title=normalized[:100],
                    description=normalized,
                    metadata={"url": urls[0]},
                )
            )
        else:
            candidates.append(
                CandidateObject(object_type="note", title=normalized[:100] or "Сохранённое", description=normalized)
            )

        return AnalysisPayload(
            provider="heuristic",
            model=None,
            summary=summary,
            proposed_type=proposed_type,
            confidence=confidence,
            needs_confirmation=needs_confirmation,
            extracted_entities=entities,
            candidates=candidates,
            draft_replies={},
            assistant_response=assistant_response,
            clarification_question=clarification_question,
            raw={"hint": hint, "context": context},
        )

    def _parse_context(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        semantic_parts: list[str] = []
        for raw_line in text.splitlines():
            line = compact_text(raw_line)
            if not line:
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                normalized_key = compact_text(key).lower()
                normalized_value = compact_text(value)
                fields[normalized_key] = normalized_value
                if normalized_key in {"user_text", "transcript", "ocr_text", "caption", "filename", "media_title"}:
                    semantic_parts.append(normalized_value)
            else:
                semantic_parts.append(line)
        semantic_text = compact_text(" ".join(semantic_parts) or text)
        fields["semantic_text"] = semantic_text
        fields.setdefault("filename", "")
        return fields

    def _voice_candidates(self, normalized: str, dates, hint: str | None) -> list[CandidateObject]:
        if hint != "voice":
            return []
        segments = [segment for segment in re.split(r",|;| а ещё | и ещё | потом ", normalized) if compact_text(segment)]
        if len(segments) < 2:
            return []
        candidates: list[CandidateObject] = []
        first_date = dates[0] if dates else None
        for segment in segments:
            piece = compact_text(segment)
            piece_lower = piece.lower()
            if any(marker in piece_lower for marker in IDEA_HINTS):
                candidates.append(CandidateObject(object_type="note", title=piece[:80], description=piece))
            elif any(marker in piece_lower for marker in REPLY_HINTS):
                candidates.append(CandidateObject(object_type="reply_later", title=piece[:80], description=piece, due_at=first_date))
            else:
                candidates.append(CandidateObject(object_type="task", title=piece[:80], description=piece, due_at=first_date))
        return candidates

    def _shopping_items(self, normalized: str, lowered: str) -> list[str]:
        if not lowered.startswith("купить "):
            return []
        raw_items = re.split(r",| и | / ", normalized[7:])
        items = [compact_text(item) for item in raw_items if compact_text(item)]
        return items if len(items) >= 2 else []

    def _looks_like_explicit_task(self, lowered: str) -> bool:
        return lowered.startswith(tuple(TASK_VERBS)) or any(f"{verb} " in lowered for verb in TASK_VERBS)

    def _looks_like_question(self, normalized: str, lowered: str, hint: str | None) -> bool:
        if hint == "voice" and self._looks_like_explicit_task(lowered):
            return False
        if "?" in normalized:
            return True
        return any(lowered.startswith(prefix) for prefix in QUESTION_WORDS)

    def _looks_like_chat_capture(self, lowered: str, context: dict[str, str]) -> bool:
        if any(marker in lowered for marker in CHAT_HINTS):
            return True
        filename = context.get("filename", "").lower()
        return "chat" in filename or "dialog" in filename or "screen" in filename

    def _build_question_answer(self, normalized: str, hint: str | None) -> str:
        if hint == "image":
            return "Похоже, во вложении содержится вопрос. Я сохранил исходник; для точного ответа использую AI-анализ изображения, а в резервном режиме лучше открыть это в Mini App и уточнить контекст."
        if "когда" in normalized.lower():
            return "Это похоже на вопрос о времени или сроке. Если во входящем нет точной даты, лучше уточнить недостающие детали перед постановкой задачи."
        if "что" in normalized.lower() or "как" in normalized.lower():
            return "Похоже, это информационный вопрос. Я сохранил контекст и отметил его как запрос на ответ; при активном AI-провайдере бот вернёт полноценный ответ сразу."
        return "Похоже, это вопрос. Я распознал его как запрос на ответ и сохранил контекст для дальнейшей работы."
