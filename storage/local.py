from __future__ import annotations

import uuid
from pathlib import Path

from storage.base import StorageAdapter
from utils.settings import get_settings


class LocalStorageAdapter(StorageAdapter):
    def __init__(self) -> None:
        self.root = get_settings().local_storage_root

    async def save_bytes(self, *, user_id: int, filename: str, content: bytes) -> Path:
        user_dir = self.root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4()}-{filename}".replace(" ", "_")
        path = user_dir / safe_name
        path.write_bytes(content)
        return path
