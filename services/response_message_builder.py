from __future__ import annotations

import re

from domain.analysis_models import ResolvedAnalysisResult
from domain.enums import ConfidenceLevel, FinalType


class ResponseMessageBuilder:
    def build(self, result: ResolvedAnalysisResult) -> str:
        if result.confidence_level == ConfidenceLevel.LOW and result.needs_user_confirmation:
            return "Я сохранил это во входящие, чтобы ничего не потерять."
        if not result.items:
            if result.primary_type == FinalType.NOTE:
                return "Похоже, это лучше сохранить как заметку."
            return "Я сохранил это во входящие, чтобы ничего не потерять."

        first = result.items[0]
        if result.primary_type == FinalType.REMINDER:
            title = self._inline_title(first.title)
            date_label = first.metadata.get("date_label")
            if date_label and date_label.lower() not in title.lower():
                return f"Похоже, это напоминание: {title} {date_label}."
            return f"Похоже, это напоминание: {title}."
        if result.primary_type == FinalType.LIST:
            if first.title == "Список покупок":
                return "Похоже, это список покупок."
            return "Похоже, это список."
        if result.primary_type == FinalType.EVENT:
            return "Похоже, это событие."
        return "Похоже, это лучше сохранить как заметку."

    def _inline_title(self, title: str) -> str:
        if not title:
            return "это"
        if re.search(r"[A-Z]", title):
            return title
        return title[:1].lower() + title[1:]