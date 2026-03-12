from __future__ import annotations

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def delete_model(self, model: type, model_id: object) -> None:
        await self.session.execute(delete(model).where(model.id == model_id))

    async def fetch_one(self, stmt: Select):
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def fetch_all(self, stmt: Select):
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def select_model(model: type) -> Select:
        return select(model)
