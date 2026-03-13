from __future__ import annotations

import re
from dataclasses import dataclass

from ai.analyzer import AIAnalyzer
from ai.base import AIProvider
from ai.confidence_rules import ConfidenceRules
from domain.action_models import ActionSuggestion
from domain.analysis_models import AIAnalysisResult, AnalysisContext, ExtractedContent, ResolvedAnalysisResult
from domain.entity_models import EntityDraft
from extractors.forwarded_message_extractor import ForwardedMessageExtractor
from extractors.metadata_extractor import MetadataExtractor
from extractors.ocr_extractor import OCRExtractor
from extractors.text_extractor import TextExtractor
from extractors.ticket_booking_parser import TicketBookingParser
from extractors.voice_transcription_extractor import VoiceTranscriptionExtractor
from input_normalizer import InputNormalizer
from services.dynamic_action_builder import DynamicActionBuilder
from services.interpretation_candidates_builder import InterpretationCandidatesBuilder
from services.minimal_object_resolver import MinimalObjectResolver
from services.response_message_builder import ResponseMessageBuilder
from utils.settings import get_settings
from utils.text import compact_text
from utils.time import now_local


@dataclass(slots=True)
class MessageInterpretationBundle:
    context: AnalysisContext
    analysis: AIAnalysisResult
    resolved: ResolvedAnalysisResult
    drafts: list[EntityDraft]
    actions: list[ActionSuggestion]
    assistant_response: str
    should_auto_create: bool


class MessageInterpretationService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider
        self.settings = get_settings()
        self.normalizer = InputNormalizer()
        self.extractors = [
            TextExtractor(),
            MetadataExtractor(),
            ForwardedMessageExtractor(),
            VoiceTranscriptionExtractor(provider),
            OCRExtractor(provider),
            TicketBookingParser(),
        ]
        self.analyzer = AIAnalyzer(provider)
        self.resolver = MinimalObjectResolver()
        self.candidates_builder = InterpretationCandidatesBuilder()
        self.action_builder = DynamicActionBuilder()
        self.response_builder = ResponseMessageBuilder()
        self.confidence_rules = ConfidenceRules()

    async def interpret(self, item, attachments=None) -> MessageInterpretationBundle:
        payload = self.normalizer.normalize(item, attachments=attachments)
        extracted = await self._extract_content(payload)
        context = AnalysisContext(now=now_local(), timezone=self.settings.timezone, payload=payload, extracted=extracted)
        analysis = await self.analyzer.analyze(context)
        resolved = self.resolver.resolve(context, analysis)
        drafts = self.candidates_builder.build(resolved)
        actions = self.action_builder.build(resolved, drafts, context.now)
        assistant_response = self.response_builder.build(resolved)
        should_auto_create = self.confidence_rules.should_auto_create(
            resolved.confidence,
            resolved.needs_user_confirmation,
            len(drafts),
        )
        return MessageInterpretationBundle(
            context=context,
            analysis=analysis,
            resolved=resolved,
            drafts=drafts,
            actions=actions,
            assistant_response=assistant_response,
            should_auto_create=should_auto_create,
        )

    async def _extract_content(self, payload) -> ExtractedContent:
        content = ExtractedContent(raw_text=payload.raw_text, caption=payload.caption, forwarded_text=payload.forwarded_text)
        seed_context = AnalysisContext(now=now_local(), timezone=self.settings.timezone, payload=payload, extracted=content)
        for extractor in self.extractors:
            content = await extractor.extract(seed_context, content)
            seed_context = AnalysisContext(now=seed_context.now, timezone=seed_context.timezone, payload=payload, extracted=content)
        content.extracted_text = self._merge_text(content)
        content.detected_language = self._detect_language(content.extracted_text or "")
        return content

    def _merge_text(self, content: ExtractedContent) -> str:
        ordered = [content.raw_text, content.forwarded_text, content.transcript, content.ocr_text]
        return compact_text("\n".join(part for part in ordered if part))

    def _detect_language(self, text: str) -> str | None:
        if not text:
            return None
        return "ru" if re.search(r"[А-Яа-яЁё]", text) else "en"
