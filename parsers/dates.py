from __future__ import annotations

from datetime import datetime

from dateparser.search import search_dates

from utils.settings import get_settings



def extract_dates(text: str) -> list[datetime]:
    matches = search_dates(
        text,
        languages=["ru", "en"],
        settings={"TIMEZONE": get_settings().timezone, "RETURN_AS_TIMEZONE_AWARE": True},
    ) or []
    return [value for _, value in matches]
