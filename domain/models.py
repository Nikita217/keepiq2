from domain.action_models import ActionSuggestion
from domain.analysis_models import (
    AIAnalysisItem,
    AIAnalysisResult,
    AnalysisContext,
    ExtractedContent,
    ExtractedEntities,
    NormalizedAttachment,
    NormalizedIncomingPayload,
    ReasoningFlags,
    RelativeOffset,
    ResolvedAnalysisItem,
    ResolvedAnalysisResult,
    StrictModel,
)
from domain.entity_models import EntityDraft

AnalysisItem = AIAnalysisItem
StructuredAnalysisResult = AIAnalysisResult
StructuredAnalysisSuggestion = ActionSuggestion

__all__ = [
    "AIAnalysisItem",
    "AIAnalysisResult",
    "ActionSuggestion",
    "AnalysisContext",
    "AnalysisItem",
    "EntityDraft",
    "ExtractedContent",
    "ExtractedEntities",
    "NormalizedAttachment",
    "NormalizedIncomingPayload",
    "ReasoningFlags",
    "RelativeOffset",
    "ResolvedAnalysisItem",
    "ResolvedAnalysisResult",
    "StrictModel",
    "StructuredAnalysisResult",
    "StructuredAnalysisSuggestion",
]
