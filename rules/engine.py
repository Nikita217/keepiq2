from __future__ import annotations

from domain.models import AnalysisContext, StructuredAnalysisResult
from rules.base import DeterministicRule
from rules.datetime_suggestion_rules import DateTimeSuggestionRule
from rules.inbox_fallback_rules import InboxFallbackRule
from rules.reply_later_rules import ReplyLaterRule
from rules.shopping_list_rules import ShoppingListRule
from rules.ticket_rules import TicketRule


class RuleEngine:
    def __init__(self, rules: list[DeterministicRule] | None = None) -> None:
        self.rules = rules or [
            ShoppingListRule(),
            TicketRule(),
            ReplyLaterRule(),
            DateTimeSuggestionRule(),
            InboxFallbackRule(),
        ]

    def apply(self, context: AnalysisContext, result: StructuredAnalysisResult) -> StructuredAnalysisResult:
        for rule in self.rules:
            result = rule.apply(context, result)
        return result

