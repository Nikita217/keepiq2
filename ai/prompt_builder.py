from __future__ import annotations

import json

from domain.models import AnalysisContext, StructuredAnalysisResult


SYSTEM_PROMPT = """
You are the structured analysis layer of a Telegram productivity assistant.
You are not a creative writer. You are a careful interpreter of incoming user data.

You must return valid JSON only and it must match the provided schema.
Do not add extra keys.
Do not invent dates, times, people, places, organizations, URLs, or event details.
If you are unsure, lower confidence, mark the item with needs_confirmation=true, and route to inbox_review.
If an input contains several meanings, split them into multiple items.
Never collapse everything into a single reminder.
Distinguish clearly:
- event: a real-world occurrence the user should not miss
- reminder: any actionable item or follow-up the user wants to remember, including answer-later cases
- list: multiple checklist items that belong together
- note: information worth keeping without scheduling
- inbox_review: not enough certainty to classify safely
""".strip()


FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "source_type": "plain_text",
            "extracted_text": "завтра купить тапки",
        },
        "output": {
            "source_type": "plain_text",
            "detected_language": "ru",
            "summary": "Нужно напомнить завтра купить тапки",
            "primary_intent": "reminder",
            "confidence": 0.9,
            "items": [
                {
                    "type": "reminder",
                    "title": "Купить тапки",
                    "description": None,
                    "datetime": None,
                    "date_only": True,
                    "priority": "medium",
                    "category": "shopping",
                    "people": [],
                    "places": [],
                    "links": [],
                    "list_items": [],
                    "needs_confirmation": True,
                    "uncertain_fields": ["datetime"],
                    "metadata": {"date_hint": "tomorrow"},
                }
            ],
            "extracted_entities": {
                "dates": [],
                "times": [],
                "people": [],
                "places": [],
                "organizations": [],
                "amounts": [],
                "urls": [],
                "ambiguous_datetimes": ["завтра"],
            },
            "user_action_suggestions": [],
            "should_store_original": True,
            "should_go_to_inbox": False,
            "reasoning_notes": "Relative day without exact time",
        },
    },
    {
        "input": {
            "source_type": "screenshot",
            "extracted_text": "Скрин переписки: можешь завтра отправить договор?",
        },
        "output": {
            "source_type": "screenshot",
            "detected_language": "ru",
            "summary": "В переписке есть просьба отправить договор",
            "primary_intent": "reminder",
            "confidence": 0.83,
            "items": [
                {
                    "type": "reminder",
                    "title": "Отправить договор",
                    "description": "Поручение из переписки",
                    "datetime": None,
                    "date_only": True,
                    "priority": "medium",
                    "category": "work",
                    "people": [],
                    "places": [],
                    "links": [],
                    "list_items": [],
                    "needs_confirmation": True,
                    "uncertain_fields": ["datetime"],
                    "metadata": {"source": "chat_screenshot"},
                }
            ],
            "extracted_entities": {
                "dates": [],
                "times": [],
                "people": [],
                "places": [],
                "organizations": [],
                "amounts": [],
                "urls": [],
                "ambiguous_datetimes": ["завтра"],
            },
            "user_action_suggestions": [],
            "should_store_original": True,
            "should_go_to_inbox": False,
            "reasoning_notes": "Chat screenshot with explicit request",
        },
    },
]


class PromptBuilder:
    prompt_version = "v1"

    def build_messages(self, context: AnalysisContext) -> list[dict[str, str]]:
        payload = {
            "source_type": context.payload.source_type.value,
            "raw_text": context.payload.raw_text,
            "caption": context.payload.caption,
            "source_url": context.payload.source_url,
            "media_type": context.payload.media_type,
            "forwarded": context.payload.forwarded,
            "metadata": context.extracted.metadata,
            "extracted_text": context.extracted.extracted_text,
            "transcript": context.extracted.transcript,
            "ocr_text": context.extracted.ocr_text,
            "source_signals": context.extracted.source_signals,
            "extraction_errors": context.extracted.extraction_errors,
            "ambiguous_datetime_phrases": context.extracted.ambiguous_datetime_phrases,
            "now": context.now.isoformat(),
            "timezone": context.timezone,
            "schema": StructuredAnalysisResult.model_json_schema(),
        }
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"examples": FEW_SHOT_EXAMPLES, "payload": payload}, ensure_ascii=False),
            },
        ]

