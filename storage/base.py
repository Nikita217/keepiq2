from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageAdapter(ABC):
    @abstractmethod
    async def save_bytes(self, *, user_id: int, filename: str, content: bytes) -> Path:
        raise NotImplementedError
