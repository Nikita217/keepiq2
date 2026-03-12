from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import IncomingItem
from models.enums import ParseStatus
from repositories.incoming import IncomingRepository
from schemas.incoming import IncomingItemRead, IncomingUpdateRequest

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("", response_model=list[IncomingItemRead])
async def list_inbox(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    repo = IncomingRepository(session)
    items = await repo.list_inbox(user.id)
    return [
        IncomingItemRead(
            id=item.id,
            incoming_type=item.incoming_type,
            parse_status=item.parse_status,
            summary=item.summary,
            proposed_type=item.proposed_type,
            confidence=item.confidence,
            needs_confirmation=item.needs_confirmation,
            raw_text=item.raw_text,
            transcript_text=item.transcript_text,
            ocr_text=item.ocr_text,
            source_url=item.source_url,
            created_at=item.created_at,
            attachments=item.attachments,
            entities=item.entities,
            logs=item.processing_logs,
        )
        for item in items
    ]


@router.patch("/{item_id}", response_model=IncomingItemRead)
async def update_inbox_item(
    item_id: UUID,
    payload: IncomingUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    item = await session.get(IncomingItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="item not found")

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    if payload.needs_confirmation is False and item.parse_status == ParseStatus.NEEDS_REVIEW.value:
        item.parse_status = ParseStatus.CONFIRMED.value
    await session.commit()
    await session.refresh(item)
    return IncomingItemRead(
        id=item.id,
        incoming_type=item.incoming_type,
        parse_status=item.parse_status,
        summary=item.summary,
        proposed_type=item.proposed_type,
        confidence=item.confidence,
        needs_confirmation=item.needs_confirmation,
        raw_text=item.raw_text,
        transcript_text=item.transcript_text,
        ocr_text=item.ocr_text,
        source_url=item.source_url,
        created_at=item.created_at,
        attachments=item.attachments,
        entities=item.entities,
        logs=item.processing_logs,
    )
