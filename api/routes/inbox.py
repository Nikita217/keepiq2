from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from models import IncomingItem
from models.enums import ParseStatus
from repositories.incoming import IncomingRepository
from schemas.incoming import InboxActionRequest, IncomingItemRead, IncomingUpdateRequest, SuggestedActionRead
from services.inbox_actions import InboxActionService

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("", response_model=list[IncomingItemRead])
async def list_inbox(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    repo = IncomingRepository(session)
    items = await repo.list_inbox(user.id)
    return [_to_read_model(item) for item in items]


@router.post("/{item_id}/resolve", response_model=IncomingItemRead)
async def resolve_inbox_item(
    item_id: UUID,
    payload: InboxActionRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        item = await InboxActionService(session).resolve(
            item_id=item_id,
            user_id=user.id,
            target_type=payload.target_type,
            title=payload.title,
            description=payload.description,
            scheduled_at=payload.scheduled_at,
            kind=payload.kind,
            source_url=payload.source_url,
            list_items=payload.list_items,
            force_confirmation=payload.force_confirmation,
            suggested_action_id=payload.suggested_action_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail="item not found") from exc
    return _to_read_model(item)


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
    return _to_read_model(item)


def _to_read_model(item: IncomingItem) -> IncomingItemRead:
    metadata = item.metadata_json or {}
    suggested_actions = [SuggestedActionRead(**action) for action in metadata.get("suggested_actions", [])]
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
        assistant_response=metadata.get("assistant_response"),
        clarification_question=metadata.get("clarification_question"),
        resolved_object_type=metadata.get("resolved_object_type"),
        suggested_actions=suggested_actions,
        created_at=item.created_at,
        attachments=item.attachments,
        entities=item.entities,
        logs=item.processing_logs,
    )

