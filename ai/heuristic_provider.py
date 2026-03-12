from __future__ import annotations

from pathlib import Path

from ai.base import AIProvider
from parsers.text import HeuristicTextParser
from schemas.ai import AnalysisPayload


class HeuristicAIProvider(AIProvider):
    provider_name = "heuristic"

    def __init__(self) -> None:
        self.parser = HeuristicTextParser()

    async def analyze_text(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        return self.parser.analyze(text, hint=hint)

    async def analyze_image(self, file_path: Path, *, extracted_text: str | None = None) -> AnalysisPayload:
        text = extracted_text or f"Изображение {file_path.name} сохранено и ждёт подтверждения"
        payload = self.parser.analyze(text, hint="image")
        payload.summary = extracted_text or "Изображение сохранено во входящие"
        payload.needs_confirmation = True
        payload.confidence = min(payload.confidence, 0.56)
        return payload

    async def transcribe_audio(self, file_path: Path) -> str:
        return f"[transcription unavailable] {file_path.name}"

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        return {
            "short": f"Принял. Вернусь с ответом позже. {text[:80]}".strip(),
            "polite": "Спасибо, увидел сообщение. Вернусь с ответом чуть позже.",
            "business": "Сообщение получил. Подготовлю ответ и вернусь к вам позже.",
            "soft": "Спасибо, я сохраню это и отвечу, когда смогу спокойно вернуться.",
            "confident": "Сообщение зафиксировал. Отвечу позже по сути.",
            "humor": "Сообщение поймал, отправляю его на аккуратную парковку до ответа.",
        }
