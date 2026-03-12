from __future__ import annotations

from ai.base import AIProvider
from ai.structured_analysis_client import StructuredAnalysisClient
from content_extractors.aggregator import ContentExtractionService
from content_extractors.forwarded_message_extractor import ForwardedMessageExtractor
from content_extractors.link_parser import LinkParserExtractor
from content_extractors.metadata_extractor import MetadataExtractor
from content_extractors.ocr_extractor import OCRExtractor
from content_extractors.text_extractor import TextExtractor
from content_extractors.ticket_booking_parser import TicketBookingParser
from content_extractors.voice_transcription_extractor import VoiceTranscriptionExtractor
from domain.models import AnalysisContext, ExtractedContent, StructuredAnalysisResult
from input_normalizer import InputNormalizer
from rules.engine import RuleEngine
from services.suggestion_service import SuggestionService
from services.user_reply_formatter import UserReplyFormatter
from utils.settings import get_settings
from utils.time import now_local


class AnalysisOrchestrator:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.normalizer = InputNormalizer()
        self.extractors = ContentExtractionService(
            [
                TextExtractor(),
                MetadataExtractor(),
                ForwardedMessageExtractor(),
                LinkParserExtractor(),
                VoiceTranscriptionExtractor(provider),
                OCRExtractor(provider),
                TicketBookingParser(),
            ]
        )
        self.client = StructuredAnalysisClient(provider)
        self.rules = RuleEngine()
        self.suggestions = SuggestionService()
        self.formatter = UserReplyFormatter()
        self.settings = get_settings()

    async def analyze(self, item, attachments=None) -> StructuredAnalysisResult:
        result, _ = await self.analyze_with_context(item, attachments=attachments)
        return result

    async def analyze_with_context(self, item, attachments=None) -> tuple[StructuredAnalysisResult, AnalysisContext]:
        payload = self.normalizer.normalize(item, attachments=attachments)
        seed_context = AnalysisContext(
            now=now_local(),
            timezone=self.settings.timezone,
            payload=payload,
            extracted=ExtractedContent(),
        )
        extracted = await self.extractors.extract(seed_context)
        context = AnalysisContext(now=seed_context.now, timezone=seed_context.timezone, payload=payload, extracted=extracted)
        result = await self.client.analyze(context)
        result = self.rules.apply(context, result)
        result.user_action_suggestions = self.suggestions.build(context, result)
        return result, context

    def build_user_response(self, result: StructuredAnalysisResult) -> str:
        return self.formatter.format(result)

