from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import ListEntity, ListItem
from repositories.lists import ListRepository
from schemas.list import ListItemRead, ListRead, ListUpdateRequest

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
                created_at=list_entity.created_at,
                updated_at=list_entity.updated_at,
                items=[ListItemRead.model_validate(item, from_attributes=True) for item in items],
            )
        )
    return result


@router.patch("/{list_id}", response_model=ListRead)
async def update_list(
    list_id: UUID,
    payload: ListUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = ListRepository(session)
    list_entity = await session.get(ListEntity, list_id)
    if list_entity is None or list_entity.user_id != user.id:
        raise HTTPException(status_code=404, detail="list not found")

    update_data = payload.model_dump(exclude_unset=True, exclude={"items"})
    for key, value in update_data.items():
        setattr(list_entity, key, value)

    if payload.items is not None:
        existing_items = {item.id: item for item in await repo.list_items(list_entity.id)}
        seen_ids: set[UUID] = set()
        for index, item_payload in enumerate(payload.items):
            sort_order = item_payload.sort_order if item_payload.sort_order is not None else index
            if item_payload.id and item_payload.id in existing_items:
                list_item = existing_items[item_payload.id]
                list_item.text = item_payload.text
                list_item.is_done = item_payload.is_done
                list_item.sort_order = sort_order
                seen_ids.add(item_payload.id)
                continue
            session.add(
                ListItem(
                    list_id=list_entity.id,
                    text=item_payload.text,
                    is_done=item_payload.is_done,
                    sort_order=sort_order,
                )
            )

        for existing_id, list_item in existing_items.items():
            if existing_id not in seen_ids:
                await session.delete(list_item)

    await session.commit()
    await session.refresh(list_entity)
    items = await repo.list_items(list_entity.id)
    return ListRead(
        id=list_entity.id,
        title=list_entity.title,
        kind=list_entity.kind,
        description=list_entity.description,
        source_incoming_item_id=list_entity.source_incoming_item_id,
        created_at=list_entity.created_at,
        updated_at=list_entity.updated_at,
        items=[ListItemRead.model_validate(item, from_attributes=True) for item in items],
    )


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    list_entity = await session.get(ListEntity, list_id)
    if list_entity is None or list_entity.user_id != user.id:
        raise HTTPException(status_code=404, detail="list not found")
    await session.delete(list_entity)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
