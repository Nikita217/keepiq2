from __future__ import annotations

from ai.base import AIProvider
from services.message_interpretation_service import MessageInterpretationBundle, MessageInterpretationService


class AnalysisService:
    def __init__(self, provider: AIProvider) -> None:
        self.interpreter = MessageInterpretationService(provider)
        self.provider = provider

    async def analyze_item(self, item, attachments=None) -> MessageInterpretationBundle:
        return await self.interpreter.interpret(item, attachments=attachments)

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        return await self.provider.generate_reply_drafts(text)
