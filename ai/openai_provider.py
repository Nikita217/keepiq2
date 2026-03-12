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
You are the AI brain of a Russian-language Telegram productivity assistant.
Your primary job is to understand what the user sent, decide whether it is a task, reminder, event, note, list, reply-later item, saved item, or a question that should be answered right now.

Return strict JSON with fields:
summary, proposed_type, confidence, needs_confirmation, extracted_entities, candidates, draft_replies, assistant_response, clarification_question, suggested_actions.

Rules:
- proposed_type must be one of: task, reminder, event, note, list, reply_later, saved, answer.
- Each candidate must contain object_type, title, description, due_at, remind_at, event_at, category_hint, items, metadata.
- Each suggested_action must contain: label, kind, target_type, due_at, remind_at, event_at, title, response_text.
- The assistant_response must be written in natural Russian, without talking about confidence or internal system details.
- Do not say "incoming saved" or "confidence".
- If the item is obviously a task, do not offer irrelevant alternatives like list/note/event just in case.
- Think about the next best user choices. Suggested actions should be adaptive and concrete.
- If this is a reminder without an exact time, suggest 2-3 realistic times.
- If this is a plain task without a date, suggest a few realistic scheduling options.
- If the item is primarily a question, use proposed_type="answer" and return the answer directly in assistant_response.
- If the item looks like a screenshot of a conversation, decide whether it needs an answer now, reply later, a task, or a note.
- Use filename, mime type, caption, transcript, OCR text, and forwarding signal as context.
- Do not invent missing dates; if uncertain, keep needs_confirmation=true.
""".strip()


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        self.audio_model = settings.openai_audio_model
        self.reasoning_effort = settings.openai_reasoning_effort
        self.fallback = HeuristicTextParser()

    async def analyze_text(self, text: str, *, hint: str | None = None) -> AnalysisPayload:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"hint={hint or ''}\ncontext={text}"},
            ],
            **self._reasoning_kwargs(self.model),
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
                        {"type": "text", "text": f"context={extracted_text or ''}"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                    ],
                },
            ],
            **self._reasoning_kwargs(self.vision_model),
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
            **self._reasoning_kwargs(self.model),
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def _reasoning_kwargs(self, model: str) -> dict:
        if model.startswith("gpt-5"):
            return {"reasoning": {"effort": self.reasoning_effort}}
        return {}
