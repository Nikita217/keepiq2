from __future__ import annotations

from utils.text import compact_text, split_lines_to_items


LIST_STARTERS = (
    "купить ",
    "список",
    "что взять",
    "идеи",
)
BLOCKING_HINTS = (
    "напом",
    "концерт",
    "встреч",
    "билет",
    "бронь",
    "завтра",
    "сегодня",
    "послезавтра",
)


def detect_list_items(text: str) -> list[str]:
    normalized = compact_text(text)
    lowered = normalized.lower()
    if lowered.startswith("купить "):
        normalized = compact_text(normalized[7:])
    return [item for item in split_lines_to_items(normalized) if item]


def looks_like_list(text: str) -> bool:
    normalized = compact_text(text)
    lowered = normalized.lower()
    items = detect_list_items(normalized)
    if len(items) < 2:
        return False
    if any(lowered.startswith(starter) for starter in LIST_STARTERS):
        return True
    if any(hint in lowered for hint in BLOCKING_HINTS):
        return False
    if len(items) >= 3 and all(len(item.split()) <= 3 for item in items):
        return True
    return False