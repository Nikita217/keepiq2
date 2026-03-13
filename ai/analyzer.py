from __future__ import annotations

import asyncio

import structlog

from ai.base import AIProvider
from ai.heuristic_provider import HeuristicAIProvider
from domain.analysis_models import AIAnalysisResult, AnalysisContext, ExtractedEntities, ReasoningFlags
from domain.enums import FinalType
from utils.settings import get_settings

logger = structlog.get_logger(__name__)


class AIAnalyzer:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.fallback = provider if isinstance(provider, HeuristicAIProvider) else HeuristicAIProvider()
        self.settings = get_settings()

    async def analyze(self, context: AnalysisContext) -> AIAnalysisResult:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.ai_max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.provider.analyze(context),
                    timeout=self.settings.ai_timeout_seconds,
                )
                return AIAnalysisResult.model_validate(result)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "ai_analysis_attempt_failed",
                    attempt=attempt,
                    provider=self.provider.provider_name,
                    error=str(exc),
                )

        if self.fallback is not self.provider:
            try:
                return await self.fallback.analyze(context)
            except Exception as exc:  # pragma: no cover
                last_error = exc

        normalized_text = context.extracted.extracted_text or context.payload.raw_text or ""
        logger.error("ai_analysis_failed_hard", provider=self.provider.provider_name, error=str(last_error) if last_error else None)
        return AIAnalysisResult(
            source_type=context.payload.source_type,
            normalized_text=normalized_text,
            summary="Не удалось уверенно разобрать сообщение",
            primary_type=FinalType.NOTE,
            secondary_candidate_type=None,
            confidence=0.0,
            needs_user_confirmation=True,
            items=[],
            extracted_entities=ExtractedEntities(),
            reasoning_flags=ReasoningFlags(),
        )
