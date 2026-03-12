from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import Task
from repositories.tasks import TaskRepository
from schemas.task import TaskRead, TaskUpdateRequest

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    tasks = await TaskRepository(session).list_all(user.id)
    return [TaskRead.model_validate(task, from_attributes=True) for task in tasks]


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    task = await session.get(Task, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="task not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(task, key, value)
    await session.commit()
    await session.refresh(task)
    return TaskRead.model_validate(task, from_attributes=True)
