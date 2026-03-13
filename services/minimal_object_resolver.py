from __future__ import annotations

from ai.confidence_rules import ConfidenceRules
from domain.analysis_models import AIAnalysisResult, AnalysisContext, ResolvedAnalysisResult
from domain.enums import FinalType
from services.datetime_resolution_service import DatetimeResolutionService


class MinimalObjectResolver:
    def __init__(self) -> None:
        self.datetime_resolution = DatetimeResolutionService()
        self.confidence_rules = ConfidenceRules()

    def resolve(self, context: AnalysisContext, analysis: AIAnalysisResult) -> ResolvedAnalysisResult:
        resolved_items = [
            self.datetime_resolution.resolve_item(context, item, index)
            for index, item in enumerate(analysis.items)
        ]

        if analysis.primary_type == FinalType.LIST and resolved_items:
            resolved_items = resolved_items[:1]
        elif analysis.reasoning_flags.contains_event_context:
            resolved_items = [item for item in resolved_items if item.type == FinalType.REMINDER] or resolved_items[:1]
        elif len(resolved_items) > 1 and not analysis.reasoning_flags.contains_multiple_independent_actions:
            resolved_items = resolved_items[:1]

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
