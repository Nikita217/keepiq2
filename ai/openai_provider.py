from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import AsyncOpenAI

from ai.base import AIProvider
from ai.heuristic_provider import HeuristicAIProvider
from ai.prompt_builder import PromptBuilder
from domain.models import AnalysisContext, AnalysisTrace, StructuredAnalysisResult
from utils.settings import get_settings


class OpenAIProvider(AIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        self.audio_model = settings.openai_audio_model
        self.reasoning_effort = settings.openai_reasoning_effort
        self.prompt_builder = PromptBuilder()
        self.fallback = HeuristicAIProvider()

    async def analyze(self, context: AnalysisContext) -> StructuredAnalysisResult:
        messages = self.prompt_builder.build_messages(context)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=messages,
                **self._reasoning_kwargs(self.model),
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            result = StructuredAnalysisResult.model_validate(payload)
            result.trace = AnalysisTrace(
                provider=self.provider_name,
                model=self.model,
                prompt_version=self.prompt_builder.prompt_version,
                raw_response={"response_id": response.id},
            )
            return result
        except Exception:
            result = await self.fallback.analyze(context)
            result.trace = AnalysisTrace(
                provider=self.provider_name,
                model=self.model,
                prompt_version=self.prompt_builder.prompt_version,
                fallback_used=True,
            )
            return result

    async def transcribe_audio(self, file_path: Path) -> str:
        with file_path.open("rb") as audio_file:
            transcript = await self.client.audio.transcriptions.create(model=self.audio_model, file=audio_file)
        return transcript.text

    async def extract_image_text(self, file_path: Path) -> str | None:
        mime = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
        encoded = base64.b64encode(file_path.read_bytes()).decode()
        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "system",
                    "content": "Extract readable text from the image. Return JSON object with one key: text.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            **self._reasoning_kwargs(self.vision_model),
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content).get("text")

    async def generate_reply_drafts(self, text: str) -> dict[str, str]:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return JSON object with keys short, polite, business, soft. Keep drafts concise.",
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

