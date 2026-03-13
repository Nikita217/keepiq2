from datetime import datetime
from zoneinfo import ZoneInfo

from domain.analysis_models import AIAnalysisItem, AIAnalysisResult, AnalysisContext, ExtractedContent, NormalizedIncomingPayload, ReasoningFlags, RelativeOffset
from domain.enums import FinalType, SourceType
from services.dynamic_action_builder import DynamicActionBuilder
from services.interpretation_candidates_builder import InterpretationCandidatesBuilder
from services.minimal_object_resolver import MinimalObjectResolver
from services.response_message_builder import ResponseMessageBuilder


def make_context(text: str) -> AnalysisContext:
    now = datetime(2026, 3, 13, 9, 0, tzinfo=ZoneInfo('Europe/Moscow'))
    return AnalysisContext(
        now=now,
        timezone='Europe/Moscow',
        payload=NormalizedIncomingPayload(user_id=1, source_type=SourceType.PLAIN_TEXT, raw_text=text),
        extracted=ExtractedContent(raw_text=text, extracted_text=text, detected_language='ru'),
    )


def test_midnight_datetime_becomes_date_only_suggestions():
    context = make_context('Я хочу накачаться, поэтому напомни мне завтра покачать пресс')
    analysis = AIAnalysisResult(
        source_type=SourceType.PLAIN_TEXT,
        normalized_text=context.extracted.extracted_text or '',
        summary='Напомнить завтра покачать пресс',
        primary_type=FinalType.REMINDER,
        secondary_candidate_type=None,
        confidence=0.95,
        needs_user_confirmation=False,
        items=[
            AIAnalysisItem(
                type=FinalType.REMINDER,
                title='Покачать пресс',
                datetime=datetime(2026, 3, 14, 0, 0, tzinfo=ZoneInfo('Europe/Moscow')),
                confidence=0.95,
            )
        ],
        reasoning_flags=ReasoningFlags(contains_background_motivation=True, contains_actionable_request=True),
    )
    resolved = MinimalObjectResolver().resolve(context, analysis)
    drafts = InterpretationCandidatesBuilder().build(resolved)
    actions = DynamicActionBuilder().build(resolved, drafts, context.now)

    assert resolved.items[0].resolved_datetime is None
    assert [action.label for action in actions] == [
        'Напомнить завтра в 10:00',
        'Напомнить завтра в 12:00',
        'Напомнить завтра в 18:00',
        'Оставить во входящих',
    ]


def test_empty_note_items_are_synthesized():
    context = make_context('скрин переписки без явного действия')
    analysis = AIAnalysisResult(
        source_type=SourceType.PLAIN_TEXT,
        normalized_text=context.extracted.extracted_text or '',
        summary='Note about a screenshot of a chat without explicit action',
        primary_type=FinalType.NOTE,
        secondary_candidate_type=None,
        confidence=0.9,
        needs_user_confirmation=False,
        items=[],
        reasoning_flags=ReasoningFlags(),
    )
    resolved = MinimalObjectResolver().resolve(context, analysis)
    drafts = InterpretationCandidatesBuilder().build(resolved)
    actions = DynamicActionBuilder().build(resolved, drafts, context.now)

    assert len(resolved.items) == 1
    assert resolved.items[0].type == FinalType.NOTE
    assert ResponseMessageBuilder().build(resolved) == 'Похоже, это лучше сохранить как заметку.'
    assert [action.label for action in actions] == ['Сохранить заметкой', 'Оставить во входящих']


def test_relative_offset_applies_to_date_only_event_context():
    context = make_context('18 мая концерт The Hatters, напомни за неделю купить билет')
    analysis = AIAnalysisResult(
        source_type=SourceType.PLAIN_TEXT,
        normalized_text=context.extracted.extracted_text or '',
        summary='Reminder to buy a ticket one week before the concert of The Hatters on May 18',
        primary_type=FinalType.REMINDER,
        secondary_candidate_type=FinalType.EVENT,
        confidence=0.95,
        needs_user_confirmation=False,
        items=[
            AIAnalysisItem(
                type=FinalType.REMINDER,
                title='Buy ticket for The Hatters concert',
                date_only=datetime(2026, 5, 18, 0, 0, tzinfo=ZoneInfo('Europe/Moscow')).date(),
                relative_offset=RelativeOffset(value=1, unit='weeks', direction='before'),
                confidence=0.95,
            )
        ],
        reasoning_flags=ReasoningFlags(contains_actionable_request=True, contains_event_context=True),
    )
    resolved = MinimalObjectResolver().resolve(context, analysis)
    drafts = InterpretationCandidatesBuilder().build(resolved)
    actions = DynamicActionBuilder().build(resolved, drafts, context.now)

    assert resolved.items[0].resolved_date.isoformat() == '2026-05-11'
    assert resolved.items[0].title == 'Купить билет на концерт The Hatters'
    assert [action.label for action in actions] == [
        'Напомнить 11 мая в 10:00',
        'Напомнить 11 мая в 12:00',
        'Напомнить 11 мая в 18:00',
        'Оставить во входящих',
    ]
