from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict:
    return await DashboardService(session).overview(user.id, date.today())
