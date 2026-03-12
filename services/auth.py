from __future__ import annotations

import hashlib
import hmac
from time import time
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from utils.settings import get_settings


class TelegramInitDataService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def verify(self, init_data: str) -> dict[str, str]:
        if not init_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="init_data missing")

        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_value = pairs.pop("hash", None)
        auth_date = int(pairs.get("auth_date", "0"))
        if not hash_value:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="hash missing")
        if int(time()) - auth_date > self.settings.init_data_max_age_seconds:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="init_data expired")

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", self.settings.bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(hash_value, calculated_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid init_data")
        return pairs
