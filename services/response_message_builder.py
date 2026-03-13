from __future__ import annotations

from domain.analysis_models import ResolvedAnalysisResult
from domain.enums import ConfidenceLevel, FinalType


class ResponseMessageBuilder:
    def build(self, result: ResolvedAnalysisResult) -> str:
        if result.confidence_level == ConfidenceLevel.LOW and result.needs_user_confirmation:
            return "Я сохранил это во входящие, чтобы ничего не потерять."
        if not result.items:
            return "Я сохранил это во входящие, чтобы ничего не потерять."

        first = result.items[0]
        if result.primary_type == FinalType.REMINDER:
            if first.metadata.get("date_label"):
                return f"Похоже, это напоминание: {first.title.lower()} {first.metadata['date_label']}."
            return f"Похоже, это напоминание: {first.title.lower()}."
        if result.primary_type == FinalType.LIST:
            if first.title == "Список покупок":
                return "Похоже, это список покупок."
            return "Похоже, это список."
        if result.primary_type == FinalType.EVENT:
            return "Похоже, это событие."
        return "Похоже, это лучше сохранить как заметку."
