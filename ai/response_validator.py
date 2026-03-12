from __future__ import annotations

from domain.models import StructuredAnalysisResult


class ResponseValidator:
    def validate(self, payload: StructuredAnalysisResult) -> StructuredAnalysisResult:
        return StructuredAnalysisResult.model_validate(payload)

    def validate_json(self, payload: dict) -> StructuredAnalysisResult:
        return StructuredAnalysisResult.model_validate(payload)

