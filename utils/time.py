from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from utils.settings import get_settings



def now_local() -> datetime:
    return datetime.now(tz=ZoneInfo(get_settings().timezone))



def to_local(dt: datetime) -> datetime:
    return dt.astimezone(ZoneInfo(get_settings().timezone))
