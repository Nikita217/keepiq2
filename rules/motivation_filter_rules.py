from __future__ import annotations

import re

from utils.text import compact_text


MOTIVATION_PATTERNS = (
    r"\bя хочу\b",
    r"\bхочу\b",
    r"\bхочу стать\b",
    r"\bхочу быть\b",
    r"\bне хочу забыть\b",
    r"\bмне надо собраться\b",
    r"\bхочу накачаться\b",
    r"\bхочу быть здоров",
)


REMINDER_BOUNDARY = re.compile(r"\b(напомни(?: мне)?|напомнить|купить|написать|позвонить|сделать|отправить|заказать|оплатить)\b", re.IGNORECASE)


def strip_background_motivation(text: str) -> tuple[str, bool]:
    normalized = compact_text(text)
    lowered = normalized.lower()
    has_motivation = any(re.search(pattern, lowered) for pattern in MOTIVATION_PATTERNS)
    if not has_motivation:
        return normalized, False
    match = REMINDER_BOUNDARY.search(normalized)
    if match:
        return compact_text(normalized[match.start():]), True
    parts = re.split(r"[,;:.]", normalized, maxsplit=1)
    if len(parts) == 2:
        return compact_text(parts[1]), True
    return normalized, True
