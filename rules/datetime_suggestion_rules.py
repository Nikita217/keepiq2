from __future__ import annotations

from datetime import date, datetime, time

from utils.settings import get_settings

MONTH_NAMES = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def default_reminder_times() -> list[time]:
    return [_parse_time(value) for value in get_settings().ai_default_reminder_times]


def default_event_times() -> list[time]:
    return [_parse_time(value) for value in get_settings().ai_default_event_times]


def combine_date_and_time(day: date, point: time, tzinfo) -> datetime:
    return datetime.combine(day, point).replace(tzinfo=tzinfo)


def human_date_label(day: date, *, today: date | None = None) -> str:
    today = today or date.today()
    if day == today:
        return "сегодня"
    if (day - today).days == 1:
        return "завтра"
    if (day - today).days == 2:
        return "послезавтра"
    return f"{day.day} {MONTH_NAMES[day.month]}"


def format_time_label(point: time) -> str:
    return point.strftime("%H:%M")


def _parse_time(raw: str) -> time:
    hour, minute = raw.split(":", 1)
    return time(hour=int(hour), minute=int(minute))
