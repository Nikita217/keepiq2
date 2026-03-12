from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import Event
from repositories.events import EventRepository
from repositories.reminders import ReminderRepository
from schemas.event import EventRead, EventUpdateRequest
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


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: UUID,
    payload: EventUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    event = await session.get(Event, event_id)
    if event is None or event.user_id != user.id:
        raise HTTPException(status_code=404, detail="event not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    await session.commit()
    await session.refresh(event)
    return EventRead.model_validate(event, from_attributes=True)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    event = await session.get(Event, event_id)
    if event is None or event.user_id != user.id:
        raise HTTPException(status_code=404, detail="event not found")
    await session.delete(event)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
