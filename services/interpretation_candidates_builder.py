from __future__ import annotations

from domain.analysis_models import ResolvedAnalysisResult
from domain.entity_models import EntityDraft


class InterpretationCandidatesBuilder:
    def build(self, result: ResolvedAnalysisResult) -> list[EntityDraft]:
        drafts: list[EntityDraft] = []
        for item in result.items:
            drafts.append(
                EntityDraft(
                    type=item.type,
                    title=item.title,
                    description=item.description,
                    list_items=item.list_items,
                    scheduled_at=item.resolved_datetime,
                    scheduled_date=item.resolved_date,
                    event_datetime=item.event_datetime,
                    source_item_index=item.source_item_index,
                    metadata=item.metadata,
                )
            )
        return drafts
