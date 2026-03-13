from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models import AIAnalysisResult, ParsedEntity
from repositories.base import BaseRepository


class AnalysisRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_result(self, result: AIAnalysisResult) -> AIAnalysisResult:
        self.session.add(result)
        await self.flush()
        return result

    async def add_entity(self, entity: ParsedEntity) -> ParsedEntity:
        self.session.add(entity)
        await self.flush()
        return entity
