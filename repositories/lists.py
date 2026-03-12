from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ListEntity, ListItem
from repositories.base import BaseRepository


class ListRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_list(self, list_entity: ListEntity) -> ListEntity:
        self.session.add(list_entity)
        await self.flush()
        return list_entity

    async def create_items(self, items: list[ListItem]) -> list[ListItem]:
        self.session.add_all(items)
        await self.flush()
        return items

    async def list_lists(self, user_id: int, limit: int = 50) -> list[ListEntity]:
        stmt = select(ListEntity).where(ListEntity.user_id == user_id).order_by(desc(ListEntity.created_at)).limit(limit)
        return await self.fetch_all(stmt)

    async def list_items(self, list_id):
        return await self.fetch_all(select(ListItem).where(ListItem.list_id == list_id).order_by(ListItem.sort_order))
