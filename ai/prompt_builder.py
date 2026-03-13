from __future__ import annotations

import json

from ai.response_schema import build_analysis_response_schema
from ai.system_prompts import INTENT_ANALYZER_SYSTEM_PROMPT
from domain.analysis_models import AnalysisContext


class PromptBuilder:
    prompt_version = "v2"

    def build_messages(self, context: AnalysisContext) -> list[dict[str, str]]:
        payload = {
            "source_type": context.payload.source_type.value,
            "raw_text": context.payload.raw_text,
            "caption": context.payload.caption,
            "forwarded_text": context.payload.forwarded_text,
            "source_url": context.payload.source_url,
            "media_type": context.payload.media_type,
            "metadata": context.extracted.metadata,
            "normalized_text": context.extracted.extracted_text or "",
            "transcript": context.extracted.transcript,
            "ocr_text": context.extracted.ocr_text,
            "detected_language": context.extracted.detected_language,
            "source_signals": context.extracted.source_signals,
            "extraction_errors": context.extracted.extraction_errors,
            "now": context.now.isoformat(),
            "timezone": context.timezone,
            "schema": build_analysis_response_schema(),
        }
        return [
            {"role": "system", "content": INTENT_ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
