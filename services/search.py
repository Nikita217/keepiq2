from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.search import SearchRepository
from schemas.search import SearchRequest, SearchResponse


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SearchRepository(session)

    async def search(self, user_id: int, request: SearchRequest) -> SearchResponse:
        return SearchResponse(items=await self.repo.search(user_id, request))
