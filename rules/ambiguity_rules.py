from __future__ import annotations

from domain.analysis_models import AIAnalysisResult
from domain.enums import ConfidenceLevel
from utils.settings import get_settings


def confidence_level_for(value: float) -> ConfidenceLevel:
    settings = get_settings()
    if value >= settings.ai_high_confidence_threshold:
        return ConfidenceLevel.HIGH
    if value >= settings.ai_medium_confidence_threshold:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def should_force_inbox(result: AIAnalysisResult) -> bool:
    if result.confidence < get_settings().ai_medium_confidence_threshold and not result.items:
        return True
    return result.needs_user_confirmation and result.confidence < get_settings().ai_medium_confidence_threshold
