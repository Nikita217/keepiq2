from __future__ import annotations

from ai.base import AIProvider
from ai.heuristic_provider import HeuristicAIProvider
from ai.openai_provider import OpenAIProvider
from utils.settings import get_settings



def build_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.openai_api_key:
        return OpenAIProvider()
    return HeuristicAIProvider()

