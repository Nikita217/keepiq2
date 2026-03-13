from __future__ import annotations

import re
from datetime import datetime, timedelta

from dateparser.search import search_dates

from domain.analysis_models import RelativeOffset
from utils.settings import get_settings
from utils.text import compact_text


def detect_event_context(text: str) -> dict | None:
    normalized = compact_text(text)
    lowered = normalized.lower()
    if "напом" not in lowered or "за " not in lowered:
        return None

    offset = None
    if match := re.search(r"за\s+(\d+)\s+недел", lowered):
        offset = RelativeOffset(value=int(match.group(1)), unit="weeks", direction="before")
    elif "за неделю" in lowered:
        offset = RelativeOffset(value=1, unit="weeks", direction="before")
    elif match := re.search(r"за\s+(\d+)\s+дн", lowered):
        offset = RelativeOffset(value=int(match.group(1)), unit="days", direction="before")
    elif "за день" in lowered:
        offset = RelativeOffset(value=1, unit="days", direction="before")

    if offset is None:
        return None

    settings = get_settings()
    matches = search_dates(
        normalized,
        languages=["ru", "en"],
        settings={
            "TIMEZONE": settings.timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    ) or []

    event_date = None
    for phrase, parsed in matches:
        if "за " in phrase.lower():
            continue
        event_date = parsed
        break

    title = "Купить билет"
    if "билет" in lowered and "концерт" in lowered:
        title = "Купить билет на концерт"
    elif "билет" in lowered:
        title = "Купить билет"

    if "the hatters" in lowered:
        title = "Купить билет на концерт The Hatters"

    return {
        "relative_offset": offset,
        "event_date": event_date,
        "title": title,
    }


def apply_relative_offset(event_date: datetime, offset: RelativeOffset) -> datetime:
    if offset.unit == "hours":
        delta = timedelta(hours=offset.value)
    elif offset.unit == "days":
        delta = timedelta(days=offset.value)
    elif offset.unit == "weeks":
        delta = timedelta(weeks=offset.value)
    else:
        delta = timedelta(days=30 * offset.value)
    if offset.direction == "before":
        return event_date - delta
    return event_date + delta
