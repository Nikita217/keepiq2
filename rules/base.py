from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import AnalysisContext, StructuredAnalysisResult


class DeterministicRule(ABC):
    @abstractmethod
    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        raise NotImplementedError

