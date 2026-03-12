from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import Reminder
from schemas.reminder import ReminderRead, ReminderUpdateRequest

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.patch("/{reminder_id}", response_model=ReminderRead)
async def update_reminder(
    reminder_id: UUID,
    payload: ReminderUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    reminder = await session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise HTTPException(status_code=404, detail="reminder not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)

    if "remind_at" in update_data and "remind_on" not in update_data:
        reminder.remind_on = update_data["remind_at"].date() if update_data["remind_at"] else None

    await session.commit()
    await session.refresh(reminder)
    return ReminderRead.model_validate(reminder, from_attributes=True)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    reminder = await session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise HTTPException(status_code=404, detail="reminder not found")
    await session.delete(reminder)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
