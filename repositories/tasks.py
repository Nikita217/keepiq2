from __future__ import annotations

from uuid import UUID

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Task
from repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, task: Task) -> Task:
        self.session.add(task)
        await self.flush()
        return task

    async def list_for_today(self, user_id: int) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(or_(Task.status.in_(["active", "scheduled", "waiting_reply"]), Task.status == "inbox"))
            .order_by(asc(Task.due_at), desc(Task.created_at))
        )
        return await self.fetch_all(stmt)

    async def get(self, task_id: UUID) -> Task | None:
        return await self.fetch_one(select(Task).where(Task.id == task_id))

    async def list_all(self, user_id: int) -> list[Task]:
        return await self.fetch_all(select(Task).where(Task.user_id == user_id).order_by(desc(Task.created_at)))
