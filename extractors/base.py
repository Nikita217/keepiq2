from __future__ import annotations

from abc import ABC, abstractmethod

from domain.analysis_models import AnalysisContext, ExtractedContent


class ContentExtractor(ABC):
    @abstractmethod
    async def extract(self, context: AnalysisContext, content: ExtractedContent) -> ExtractedContent:
        raise NotImplementedError
