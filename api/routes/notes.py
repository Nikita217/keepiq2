from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import Note, ReplyLaterItem, SavedItem
from repositories.notes import NoteRepository
from schemas.note import (
    NoteRead,
    NoteUpdateRequest,
    ReplyLaterRead,
    ReplyLaterUpdateRequest,
    SavedItemRead,
    SavedItemUpdateRequest,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
async def list_notes(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict:
    repo = NoteRepository(session)
    notes = await repo.list_notes(user.id)
    reply_later = await repo.list_reply_later(user.id)
    saved = await repo.list_saved(user.id)
    return {
        "notes": [NoteRead.model_validate(note, from_attributes=True) for note in notes],
        "reply_later": [
            ReplyLaterRead(
                id=item.id,
                title=item.title,
                conversation_summary=item.conversation_summary,
                reply_due_at=item.reply_due_at,
                status=item.status,
                suggested_replies=item.suggested_replies_json,
                source_incoming_item_id=item.source_incoming_item_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in reply_later
        ],
        "saved": [SavedItemRead.model_validate(item, from_attributes=True) for item in saved],
    }


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: UUID,
    payload: NoteUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    note = await session.get(Note, note_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="note not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, key, value)

    await session.commit()
    await session.refresh(note)
    return NoteRead.model_validate(note, from_attributes=True)


@router.patch("/reply-later/{item_id}", response_model=ReplyLaterRead)
async def update_reply_later(
    item_id: UUID,
    payload: ReplyLaterUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    item = await session.get(ReplyLaterItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="reply later item not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)
    return ReplyLaterRead(
        id=item.id,
        title=item.title,
        conversation_summary=item.conversation_summary,
        reply_due_at=item.reply_due_at,
        status=item.status,
        suggested_replies=item.suggested_replies_json,
        source_incoming_item_id=item.source_incoming_item_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.patch("/saved/{item_id}", response_model=SavedItemRead)
async def update_saved_item(
    item_id: UUID,
    payload: SavedItemUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    item = await session.get(SavedItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="saved item not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)
    return SavedItemRead.model_validate(item, from_attributes=True)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    note = await session.get(Note, note_id)
    if note is None or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="note not found")
    await session.delete(note)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/reply-later/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reply_later(
    item_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    item = await session.get(ReplyLaterItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="reply later item not found")
    await session.delete(item)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/saved/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_item(
    item_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    item = await session.get(SavedItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="saved item not found")
    await session.delete(item)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
