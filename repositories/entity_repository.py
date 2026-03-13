from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from domain.entity_models import EntityDraft
from services.object_builder import ObjectBuilderService


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.builder = ObjectBuilderService(session)

    async def materialize(self, *, user_id: int, incoming_item_id, drafts: list[EntityDraft], upsert: bool = False):
        return await self.builder.materialize_drafts(
            user_id=user_id,
            incoming_item_id=incoming_item_id,
            drafts=drafts,
            upsert=upsert,
        )
