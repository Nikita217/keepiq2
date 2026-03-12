from __future__ import annotations

import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

from parsers.dates import extract_dates
from parsers.tickets import looks_like_ticket
from schemas.ai import AnalysisPayload, CandidateObject, ExtractedEntity, SuggestedAction
from utils.text import compact_text, split_lines_to_items
from utils.time import now_local


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
TIME_HINTS = ["утром", "днем", "днём", "вечером", "ночью", "в ", "до "]


class HeuristicTextParser:
    def analyze(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        context = self._parse_context(text)
        normalized = context["semantic_text"]
        lowered = normalized.lower()
        dates = extract_dates(normalized)
        explicit_time = self._has_explicit_time(normalized)
        entities: list[ExtractedEntity] = []
        candidates: list[CandidateObject] = []
        suggested_actions: list[SuggestedAction] = []
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
            confidence = 0.86
            needs_confirmation = False
            assistant_response = self._build_question_answer(normalized, hint)
            summary = "Похоже, здесь нужен ответ"
            suggested_actions = [
                SuggestedAction(label="Сохранить как заметку", target_type="note", title=normalized[:80] or "Вопрос"),
                SuggestedAction(label="Вернуться позже", target_type="reply_later", title=normalized[:80] or "Нужно ответить"),
            ]
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
            confidence = 0.87
            needs_confirmation = not dates or not explicit_time
            candidates = voice_candidates
            summary = f"Похоже, в сообщении {len(voice_candidates)} отдельных пункта"
            assistant_response = "Похоже, это несколько задач из одного сообщения. Я могу добавить их в задачник сразу или поставить общий срок."
            suggested_actions = self._build_time_actions(
                object_type="task",
                title="Добавить задачи",
                base_dt=dates[0] if dates else None,
                explicit_time=explicit_time,
                primary_label="Добавить все задачи",
            )
        elif looks_like_ticket(normalized) or hint in {"ticket", "booking"}:
            proposed_type = "event"
            confidence = 0.87
            needs_confirmation = not dates or not explicit_time
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
            assistant_response = "Похоже, это билет или бронь. Я могу сохранить это как событие и добавить напоминание."
            suggested_actions = self._build_time_actions(
                object_type="event",
                title="Событие",
                base_dt=dates[0] if dates else None,
                explicit_time=explicit_time,
                primary_label="Сохранить событие",
            )
        elif self._looks_like_chat_capture(lowered, context) or any(word in lowered for word in REPLY_HINTS) or hint == "forwarded":
            proposed_type = "reply_later"
            confidence = 0.83
            needs_confirmation = True
            candidates.append(
                CandidateObject(
                    object_type="reply_later",
                    title=normalized[:80] or "Вернуться к сообщению",
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
            assistant_response = "Похоже, к этому сообщению стоит вернуться позже. Могу сразу поставить удобное время для ответа."
            suggested_actions = self._build_time_actions(
                object_type="reply_later",
                title=normalized[:80] or "Вернуться к сообщению",
                base_dt=dates[0] if dates else None,
                explicit_time=explicit_time,
                primary_label="Вернуться позже",
            )
        elif lowered.startswith("напомни") or "не забыть" in lowered or "напомнить" in lowered:
            proposed_type = "reminder"
            confidence = 0.88 if dates else 0.76
            needs_confirmation = not dates or not explicit_time
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
            assistant_response = f"Похоже, это напоминание про «{title or 'это дело'}»."
            if not dates:
                assistant_response += " Я могу сразу предложить удобное время."
            elif not explicit_time:
                assistant_response += " День понятен, осталось выбрать время."
            else:
                assistant_response += " Могу сразу сохранить его как напоминание."
            suggested_actions = self._build_time_actions(
                object_type="reminder",
                title=title or "Напоминание",
                base_dt=dates[0] if dates else None,
                explicit_time=explicit_time,
                primary_label="Поставить напоминание",
            )
        elif shopping_items:
            proposed_type = "list"
            confidence = 0.86
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
            assistant_response = "Похоже, это список покупок. Сохраняю его как список, чтобы ничего не потерялось."
            suggested_actions = [SuggestedAction(label="Сохранить списком", target_type="list")]
        elif len(split_lines_to_items(normalized)) >= 3 and any(verb in lowered for verb in TASK_VERBS):
            proposed_type = "list"
            confidence = 0.82
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
            assistant_response = "Здесь вижу несколько пунктов, так что логичнее сохранить это списком."
            suggested_actions = [SuggestedAction(label="Сохранить список", target_type="list")]
        elif any(marker in lowered for marker in IDEA_HINTS):
            proposed_type = "note"
            confidence = 0.74
            needs_confirmation = False
            candidates.append(CandidateObject(object_type="note", title=normalized[:80], description=normalized))
            assistant_response = "Похоже, это заметка или мысль на потом. Сохраняю как заметку."
            suggested_actions = [SuggestedAction(label="Сохранить заметку", target_type="note")]
        elif self._looks_like_explicit_task(lowered):
            proposed_type = "task"
            confidence = 0.84
            needs_confirmation = not dates or not explicit_time
            title = normalized[:100]
            candidates.append(
                CandidateObject(
                    object_type="task",
                    title=title,
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
            assistant_response = f"Похоже, это задача «{title}»."
            if not dates:
                assistant_response += " Могу просто добавить её в задачи или сразу поставить удобный срок."
            elif not explicit_time:
                assistant_response += " День понятен, осталось выбрать время."
            else:
                assistant_response += " Могу сразу сохранить её с этим сроком."
            suggested_actions = self._build_time_actions(
                object_type="task",
                title=title,
                base_dt=dates[0] if dates else None,
                explicit_time=explicit_time,
                primary_label="Добавить задачу",
            )
        elif urls:
            proposed_type = "saved"
            confidence = 0.75
            needs_confirmation = False
            candidates.append(
                CandidateObject(
                    object_type="saved",
                    title=normalized[:100],
                    description=normalized,
                    metadata={"url": urls[0]},
                )
            )
            assistant_response = "Похоже, это ссылка, которую стоит сохранить отдельно."
            suggested_actions = [SuggestedAction(label="Сохранить ссылку", target_type="saved")]
        else:
            proposed_type = "note"
            confidence = 0.56
            needs_confirmation = True
            candidates.append(
                CandidateObject(object_type="note", title=normalized[:100] or "Сохранённое", description=normalized)
            )
            assistant_response = "Я не вижу здесь явной задачи, но могу сохранить это как заметку или помочь уточнить формат."
            suggested_actions = [
                SuggestedAction(label="Сохранить заметку", target_type="note"),
                SuggestedAction(label="Как задачу", target_type="task"),
            ]

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
            suggested_actions=suggested_actions,
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
            return "Похоже, во вложении есть вопрос. Я постарался понять его по контексту; если захочешь, можно ещё сохранить это как заметку или вернуться позже."
        if "когда" in normalized.lower():
            return "Похоже, здесь вопрос про срок или время. Если в сообщении не хватает точной даты, лучше сначала уточнить её, а потом уже ставить задачу или напоминание."
        if "что" in normalized.lower() or "как" in normalized.lower():
            return "Похоже, это вопрос, а не задача. Я отвечу на него как на запрос и при необходимости помогу сохранить результат отдельно."
        return "Похоже, это вопрос. Отвечаю по смыслу и при желании могу ещё сохранить контекст отдельно."

    def _has_explicit_time(self, normalized: str) -> bool:
        lowered = normalized.lower()
        if re.search(r"\b\d{1,2}[:.]\d{2}\b", lowered):
            return True
        return any(hint in lowered for hint in TIME_HINTS)

    def _build_time_actions(
        self,
        *,
        object_type: str,
        title: str,
        base_dt: datetime | None,
        explicit_time: bool,
        primary_label: str,
    ) -> list[SuggestedAction]:
        actions = [SuggestedAction(label=primary_label, target_type=object_type, title=title)]
        for label, dt in self._suggest_times(base_dt=base_dt, explicit_time=explicit_time):
            kwargs = {"label": label, "target_type": object_type, "title": title}
            if object_type == "task":
                kwargs["due_at"] = dt
            elif object_type == "reminder":
                kwargs["remind_at"] = dt
            elif object_type == "event":
                kwargs["event_at"] = dt
            else:
                kwargs["due_at"] = dt
            actions.append(SuggestedAction(**kwargs))
        return actions[:4]

    def _suggest_times(self, *, base_dt: datetime | None, explicit_time: bool) -> list[tuple[str, datetime]]:
        now = now_local()
        suggestions: list[tuple[str, datetime]] = []
        if base_dt is not None and explicit_time:
            return suggestions
        if base_dt is not None:
            for hour in (9, 14, 19):
                candidate = base_dt.replace(hour=hour, minute=0, second=0, microsecond=0)
                suggestions.append((f"В {hour:02d}:00", candidate))
            return suggestions

        today_evening = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if today_evening <= now:
            today_evening = today_evening + timedelta(days=1)
        tomorrow_morning = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        next_weekday = self._next_weekday(now, weekday=0).replace(hour=9, minute=0, second=0, microsecond=0)
        suggestions.append(("Сегодня к 19:00", today_evening))
        suggestions.append(("Завтра в 09:00", tomorrow_morning))
        suggestions.append(("В ближайший понедельник", next_weekday))
        return suggestions

    def _next_weekday(self, source: datetime, *, weekday: int) -> datetime:
        days_ahead = (weekday - source.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return source + timedelta(days=days_ahead)
