from __future__ import annotations

from domain.enums import ConfidenceLevel
from utils.settings import get_settings


class ConfidenceRules:
    def __init__(self) -> None:
        settings = get_settings()
        self.high_threshold = settings.ai_high_confidence_threshold
        self.medium_threshold = settings.ai_medium_confidence_threshold

    def level_for(self, confidence: float) -> ConfidenceLevel:
        if confidence >= self.high_threshold:
            return ConfidenceLevel.HIGH
        if confidence >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def should_auto_create(self, confidence: float, needs_confirmation: bool, item_count: int) -> bool:
        if needs_confirmation or item_count == 0:
            return False
        return self.level_for(confidence) == ConfidenceLevel.HIGH
