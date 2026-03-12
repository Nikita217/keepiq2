from __future__ import annotations

from ai.base import AIProvider


class ReplyDraftService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def build(self, text: str) -> dict[str, str]:
        return await self.provider.generate_reply_drafts(text)
