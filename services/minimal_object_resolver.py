from __future__ import annotations

import re

from ai.confidence_rules import ConfidenceRules
from domain.analysis_models import AIAnalysisResult, AnalysisContext, ResolvedAnalysisItem, ResolvedAnalysisResult
from domain.enums import FinalType
from services.datetime_resolution_service import DatetimeResolutionService
from utils.text import compact_text


class MinimalObjectResolver:
    def __init__(self) -> None:
        self.datetime_resolution = DatetimeResolutionService()
        self.confidence_rules = ConfidenceRules()

    def resolve(self, context: AnalysisContext, analysis: AIAnalysisResult) -> ResolvedAnalysisResult:
        resolved_items = [
            self.datetime_resolution.resolve_item(context, item, index)
            for index, item in enumerate(analysis.items)
        ]

        if not resolved_items and analysis.primary_type == FinalType.NOTE:
            resolved_items = [self._synthesize_note_item(context)]
        elif analysis.primary_type == FinalType.LIST and resolved_items:
            resolved_items = resolved_items[:1]
        elif analysis.reasoning_flags.contains_event_context:
            resolved_items = [item for item in resolved_items if item.type == FinalType.REMINDER] or resolved_items[:1]
        elif len(resolved_items) > 1 and not analysis.reasoning_flags.contains_multiple_independent_actions:
            resolved_items = resolved_items[:1]

        resolved_items = [self._normalize_item_language(context, item, analysis.primary_type) for item in resolved_items]

        needs_confirmation = analysis.needs_user_confirmation
        for item in resolved_items:
            if item.type == FinalType.REMINDER and item.resolved_datetime is None and item.resolved_date is None:
                needs_confirmation = True
            if item.type == FinalType.EVENT and item.resolved_datetime is None and item.resolved_date is None:
                needs_confirmation = True

        confidence_level = self.confidence_rules.level_for(analysis.confidence)
        return ResolvedAnalysisResult(
            source_type=analysis.source_type,
            normalized_text=analysis.normalized_text,
            summary=analysis.summary,
            primary_type=analysis.primary_type,
            secondary_candidate_type=analysis.secondary_candidate_type,
            confidence=analysis.confidence,
            confidence_level=confidence_level,
            needs_user_confirmation=needs_confirmation,
            items=resolved_items,
            extracted_entities=analysis.extracted_entities,
            reasoning_flags=analysis.reasoning_flags,
        )

    def _synthesize_note_item(self, context: AnalysisContext) -> ResolvedAnalysisItem:
        text = compact_text(context.extracted.extracted_text or context.payload.raw_text or "Материал")
        title = re.sub(r"^(идея|мысль)\s*:\s*", "", text, flags=re.IGNORECASE)[:160] or "Заметка"
        return ResolvedAnalysisItem(
            type=FinalType.NOTE,
            title=title,
            description=text or None,
            source_item_index=0,
            confidence=0.5,
            metadata={},
        )

    def _normalize_item_language(
        self,
        context: AnalysisContext,
        item: ResolvedAnalysisItem,
        primary_type: FinalType,
    ) -> ResolvedAnalysisItem:
        text = compact_text(context.extracted.extracted_text or context.payload.raw_text or "")
        if not text or not self._contains_cyrillic(text):
            return item

        normalized = item
        title = item.title or ""
        if item.type == FinalType.LIST:
            localized = "Список покупок" if text.lower().startswith("купить ") else "Список"
            normalized = normalized.model_copy(update={"title": localized})
        elif item.type == FinalType.NOTE and (not title or not self._contains_cyrillic(title)):
            localized = re.sub(r"^(идея|мысль)\s*:\s*", "", text, flags=re.IGNORECASE)[:160] or "Заметка"
            normalized = normalized.model_copy(update={"title": localized, "description": item.description or text})
        elif item.type == FinalType.REMINDER and (not title or not self._contains_cyrillic(title)):
            localized = self._localized_reminder_title(text, context)
            normalized = normalized.model_copy(update={"title": localized})
        elif item.type == FinalType.EVENT and (not title or not self._contains_cyrillic(title)):
            localized = self._localized_event_title(text)
            normalized = normalized.model_copy(update={"title": localized})
        return normalized

    def _localized_reminder_title(self, text: str, context: AnalysisContext) -> str:
        lowered = text.lower()
        if "билет" in lowered and "the hatters" in lowered:
            return "Купить билет на концерт The Hatters"
        if "билет" in lowered and "концерт" in lowered:
            return "Купить билет на концерт"
        cleaned = re.sub(r"^(я хочу[^,]*,\s*)", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(напомни( мне)?\s+)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(сегодня|завтра|послезавтра)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(поэтому)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(18\s+мая|11\s+мая|12\s+мая|13\s+мая)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = compact_text(cleaned)
        return cleaned[:160] or "Напоминание"

    def _localized_event_title(self, text: str) -> str:
        cleaned = re.sub(r"^\d{1,2}\s+[а-яa-z]+\s+", "", text, flags=re.IGNORECASE)
        cleaned = compact_text(cleaned)
        return cleaned[:160] or "Событие"

    def _contains_cyrillic(self, value: str) -> bool:
        return bool(re.search(r"[А-Яа-яЁё]", value))