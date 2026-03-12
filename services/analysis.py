from __future__ import annotations

from ai.base import AIProvider
from domain.models import StructuredAnalysisResult
from services.analysis_orchestrator import AnalysisOrchestrator


class AnalysisService:
    def __init__(self, provider: AIProvider) -> None:
        self.orchestrator = AnalysisOrchestrator(provider)
        self.provider = provider

    async def analyze_item(self, item, attachments=None) -> StructuredAnalysisResult:
        return await self.orchestrator.analyze(item, attachments=attachments)

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        return await self.provider.generate_reply_drafts(text)

    def build_user_response(self, result: StructuredAnalysisResult) -> str:
        return self.orchestrator.build_user_response(result)

