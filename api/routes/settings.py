from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from services.digests import DigestService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/digests")
async def digest_preview(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict:
    service = DigestService(session)
    return {
        "morning": await service.build_morning_digest(user.id, date.today()),
        "evening": await service.build_evening_digest(user.id, date.today()),
    }
