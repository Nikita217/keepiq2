from __future__ import annotations

import asyncio

import structlog

from ai.base import AIProvider
from ai.confidence_mapper import ConfidenceMapper
from ai.response_validator import ResponseValidator
from domain.enums import IntentType
from domain.models import AnalysisContext, AnalysisTrace, StructuredAnalysisResult
from utils.settings import get_settings

logger = structlog.get_logger(__name__)


class StructuredAnalysisClient:
    def __init__(
        self,
        provider: AIProvider,
        *,
        validator: ResponseValidator | None = None,
        confidence_mapper: ConfidenceMapper | None = None,
    ) -> None:
        self.provider = provider
        self.validator = validator or ResponseValidator()
        self.confidence_mapper = confidence_mapper or ConfidenceMapper()
        settings = get_settings()
        self.timeout_seconds = settings.ai_timeout_seconds
        self.max_retries = settings.ai_max_retries

    async def analyze(self, context: AnalysisContext) -> StructuredAnalysisResult:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await asyncio.wait_for(self.provider.analyze(context), timeout=self.timeout_seconds)
                validated = self.validator.validate(result)
                validated.confidence_level = self.confidence_mapper.map(validated.confidence)
                return validated
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "ai_analysis_attempt_failed",
                    attempt=attempt,
                    provider=self.provider.provider_name,
                    error=str(exc),
                )
        return StructuredAnalysisResult(
            source_type=context.payload.source_type,
            detected_language=None,
            summary="Не удалось уверенно разобрать входящий объект",
            primary_intent=IntentType.INBOX_REVIEW,
            confidence=0.0,
            confidence_level=self.confidence_mapper.map(0.0),
            items=[],
            should_store_original=True,
            should_go_to_inbox=True,
            reasoning_notes="AI provider failed, fallback to inbox review",
            trace=AnalysisTrace(
                provider=self.provider.provider_name,
                fallback_used=True,
                error=str(last_error) if last_error else "unknown_error",
                raw_response={},
            ),
        )

