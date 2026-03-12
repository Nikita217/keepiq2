from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from repositories.lists import ListRepository
from schemas.list import ListItemRead, ListRead

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("", response_model=list[ListRead])
async def list_lists(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    repo = ListRepository(session)
    lists = await repo.list_lists(user.id)
    result: list[ListRead] = []
    for list_entity in lists:
        items = await repo.list_items(list_entity.id)
        result.append(
            ListRead(
                id=list_entity.id,
                title=list_entity.title,
                kind=list_entity.kind,
                description=list_entity.description,
                source_incoming_item_id=list_entity.source_incoming_item_id,
                items=[ListItemRead.model_validate(item, from_attributes=True) for item in items],
            )
        )
    return result
