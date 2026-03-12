from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import urlparse

from parsers.dates import extract_dates
from parsers.tickets import looks_like_ticket
from schemas.ai import AnalysisPayload, CandidateObject, ExtractedEntity
from utils.text import compact_text, split_lines_to_items


TASK_VERBS = ["купить", "отправить", "написать", "позвонить", "сделать", "оплатить"]
REPLY_HINTS = ["ответить", "reply", "перепис", "сообщени", "чат", "вернуться"]
IDEA_HINTS = ["идея", "мысль", "референс", "сохранить", "заметка"]


class HeuristicTextParser:
    def analyze(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        normalized = compact_text(text)
        lowered = normalized.lower()
        dates = extract_dates(normalized)
        entities: list[ExtractedEntity] = []
        candidates: list[CandidateObject] = []
        proposed_type = "saved"
        summary = normalized[:180] if normalized else "Пустой ввод"
        confidence = 0.45
        needs_confirmation = True

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

        voice_candidates = self._voice_candidates(normalized, lowered, dates, hint)
        shopping_items = self._shopping_items(normalized, lowered)

        if voice_candidates:
            proposed_type = "task"
            confidence = 0.86
            needs_confirmation = False
            candidates = voice_candidates
            summary = f"Выделил {len(voice_candidates)} объекта из одного голосового"
        elif looks_like_ticket(normalized) or hint in {"ticket", "booking"}:
            proposed_type = "event"
            confidence = 0.84
            candidates.append(
                CandidateObject(
                    object_type="event",
                    title="Событие из билета" if len(normalized) > 60 else normalized,
                    description=normalized,
                    event_at=dates[0] if dates else None,
                    metadata={"kind": "ticket_or_booking"},
                )
            )
            if dates:
                candidates.append(
                    CandidateObject(
                        object_type="reminder",
                        title="Напоминание о событии",
                        remind_at=dates[0] - timedelta(hours=3),
                        description="Автопредложение напоминания за 3 часа",
                    )
                )
        elif any(word in lowered for word in REPLY_HINTS) or hint == "forwarded":
            proposed_type = "reply_later"
            confidence = 0.76
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
            confidence = 0.87 if dates else 0.68
            needs_confirmation = not bool(dates)
            title = normalized.replace("напомни", "").replace("напомнить", "").strip(" :.-")
            candidates.append(
                CandidateObject(
                    object_type="task",
                    title=title or "Напоминание",
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
            candidates.append(
                CandidateObject(
                    object_type="reminder",
                    title=title or "Напоминание",
                    remind_at=dates[0] if dates else None,
                    description=normalized,
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
            confidence = 0.79
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
        elif any(verb in lowered for verb in TASK_VERBS):
            proposed_type = "task"
            confidence = 0.69
            candidates.append(
                CandidateObject(
                    object_type="task",
                    title=normalized[:100],
                    description=normalized,
                    due_at=dates[0] if dates else None,
                )
            )
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
            raw={"hint": hint},
        )

    def _voice_candidates(self, normalized: str, lowered: str, dates, hint: str | None) -> list[CandidateObject]:
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
