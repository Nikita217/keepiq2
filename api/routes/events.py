from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from repositories.events import EventRepository
from repositories.reminders import ReminderRepository
from schemas.event import EventRead
from schemas.reminder import ReminderRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events_and_reminders(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict:
    event_repo = EventRepository(session)
    reminder_repo = ReminderRepository(session)
    events = await event_repo.list_all(user.id)
    reminders = await reminder_repo.list_all(user.id)
    return {
        "events": [EventRead.model_validate(event, from_attributes=True) for event in events],
        "reminders": [ReminderRead.model_validate(reminder, from_attributes=True) for reminder in reminders],
    }
