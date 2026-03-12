from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from schemas.search import SearchRequest, SearchResponse
from services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_items(
    payload: SearchRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    return await SearchService(session).search(user.id, payload)
