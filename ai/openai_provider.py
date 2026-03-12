from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import AsyncOpenAI

from ai.base import AIProvider
from parsers.text import HeuristicTextParser
from schemas.ai import AnalysisPayload
from utils.settings import get_settings


ANALYSIS_SYSTEM_PROMPT = """
You classify personal inbox items for a Telegram assistant.
Return strict JSON with fields:
summary, proposed_type, confidence, needs_confirmation, extracted_entities, candidates, draft_replies.
proposed_type must be one of: task, reminder, event, note, list, reply_later, saved.
Each candidate must contain object_type, title, description, due_at, remind_at, event_at, category_hint, items, metadata.
Do not invent missing dates. If uncertain, set needs_confirmation=true and lower confidence.
""".strip()


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        self.audio_model = settings.openai_audio_model
        self.fallback = HeuristicTextParser()

    async def analyze_text(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"hint={hint or ''}\ntext={text}"},
            ],
        )
        try:
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            payload.setdefault("provider", "openai")
            payload.setdefault("model", self.model)
            payload.setdefault("raw", {"response_id": response.id})
            return AnalysisPayload(**payload)
        except Exception:
            fallback = self.fallback.analyze(text, hint=hint)
            fallback.provider = "openai-fallback"
            fallback.model = self.model
            return fallback

    async def analyze_image(self, file_path: Path, *, extracted_text: str | None = None) -> AnalysisPayload:
        mime = "image/jpeg"
        if file_path.suffix.lower() == ".png":
            mime = "image/png"
        encoded = base64.b64encode(file_path.read_bytes()).decode()
        response = await self.client.chat.completions.create(
            model=self.vision_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"ocr_hint={extracted_text or ''}"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                    ],
                },
            ],
        )
        try:
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            payload.setdefault("provider", "openai")
            payload.setdefault("model", self.vision_model)
            payload.setdefault("raw", {"response_id": response.id})
            return AnalysisPayload(**payload)
        except Exception:
            fallback = self.fallback.analyze(extracted_text or file_path.name, hint="image")
            fallback.provider = "openai-fallback"
            fallback.model = self.vision_model
            return fallback

    async def transcribe_audio(self, file_path: Path) -> str:
        with file_path.open("rb") as audio_file:
            transcript = await self.client.audio.transcriptions.create(model=self.audio_model, file=audio_file)
        return transcript.text

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return JSON object with reply styles: short, polite, business, soft, confident, humor.",
                },
                {"role": "user", "content": text},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
