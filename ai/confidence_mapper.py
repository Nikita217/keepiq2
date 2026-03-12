from __future__ import annotations

from domain.enums import ConfidenceLevel
from utils.settings import get_settings


class ConfidenceMapper:
    def __init__(self) -> None:
        settings = get_settings()
        self.high_threshold = settings.ai_high_confidence_threshold
        self.medium_threshold = settings.ai_medium_confidence_threshold

    def map(self, confidence: float) -> ConfidenceLevel:
        if confidence >= self.high_threshold:
            return ConfidenceLevel.HIGH
        if confidence >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

