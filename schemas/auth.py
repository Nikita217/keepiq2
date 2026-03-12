from __future__ import annotations

from pydantic import BaseModel


class InitDataVerifyRequest(BaseModel):
    init_data: str


class SessionResponse(BaseModel):
    telegram_user_id: int
    first_name: str | None = None
    username: str | None = None
