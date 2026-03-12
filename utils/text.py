from __future__ import annotations

import re
from typing import Iterable



def compact_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()



def split_lines_to_items(value: str) -> list[str]:
    chunks = re.split(r"[\n,;•]+", value)
    return [compact_text(chunk) for chunk in chunks if compact_text(chunk)]



def build_search_blob(parts: Iterable[str | None]) -> str:
    return " ".join(compact_text(part) for part in parts if compact_text(part)).strip()
