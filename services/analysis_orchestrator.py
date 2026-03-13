from __future__ import annotations

from ai.base import AIProvider
from services.message_interpretation_service import MessageInterpretationBundle, MessageInterpretationService


class AnalysisOrchestrator:
    def __init__(self, provider: AIProvider) -> None:
        self.service = MessageInterpretationService(provider)

    async def analyze_with_context(self, item, attachments=None) -> tuple[MessageInterpretationBundle, object]:
        bundle = await self.service.interpret(item, attachments=attachments)
        return bundle, bundle.context

    async def analyze(self, item, attachments=None):
        return await self.service.interpret(item, attachments=attachments)

    def build_user_response(self, bundle: MessageInterpretationBundle) -> str:
        return bundle.assistant_response
