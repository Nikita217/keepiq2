from __future__ import annotations

import json

from fastapi import APIRouter

from schemas.auth import InitDataVerifyRequest, SessionResponse
from services.auth import TelegramInitDataService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=SessionResponse)
def verify_init_data(payload: InitDataVerifyRequest) -> SessionResponse:
    pairs = TelegramInitDataService().verify(payload.init_data)
    user = json.loads(pairs.get("user", "{}"))
    return SessionResponse(
        telegram_user_id=int(user["id"]),
        first_name=user.get("first_name"),
        username=user.get("username"),
    )
