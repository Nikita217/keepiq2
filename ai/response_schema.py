from __future__ import annotations

from domain.analysis_models import AIAnalysisResult


def build_analysis_response_schema() -> dict:
    return AIAnalysisResult.model_json_schema()
