from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_db_session
from schemas.object_actions import ObjectConvertRequest, ObjectConvertResponse
from services.object_mutations import ObjectMutationService

router = APIRouter(prefix="/objects", tags=["objects"])


@router.post("/convert", response_model=ObjectConvertResponse)
async def convert_object(
    payload: ObjectConvertRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        created = await ObjectMutationService(session).convert(
            user_id=user.id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            target_type=payload.target_type,
            title=payload.title,
            description=payload.description,
            scheduled_at=payload.scheduled_at,
            kind=payload.kind,
            source_url=payload.source_url,
            list_items=payload.list_items,
        )
    except LookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ObjectConvertResponse(object_type=payload.target_type, object_id=created.id)
