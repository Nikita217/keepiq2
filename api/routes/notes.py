from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from repositories.notes import NoteRepository
from schemas.note import NoteRead, SavedItemRead

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
            {
                "id": str(item.id),
                "title": item.title,
                "conversation_summary": item.conversation_summary,
                "reply_due_at": item.reply_due_at.isoformat() if item.reply_due_at else None,
                "status": item.status,
                "suggested_replies": item.suggested_replies_json,
                "source_incoming_item_id": str(item.source_incoming_item_id) if item.source_incoming_item_id else None,
            }
            for item in reply_later
        ],
        "saved": [SavedItemRead.model_validate(item, from_attributes=True) for item in saved],
    }
