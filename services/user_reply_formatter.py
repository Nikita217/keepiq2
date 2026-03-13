from __future__ import annotations

from domain.enums import IntentType
from domain.models import StructuredAnalysisResult


class UserReplyFormatter:
    def format(self, result: StructuredAnalysisResult) -> str:
        if result.should_go_to_inbox:
            return "Не до конца понял формат. Я оставил это во входящих, а ниже можно быстро выбрать, как сохранить."
        if not result.items:
            return result.summary
        if len(result.items) > 1:
            reminder_count = sum(1 for item in result.items if item.type == IntentType.REMINDER)
            note_count = sum(1 for item in result.items if item.type == IntentType.NOTE)
            list_count = sum(1 for item in result.items if item.type == IntentType.LIST)
            event_count = sum(1 for item in result.items if item.type == IntentType.EVENT)
            parts: list[str] = []
            if reminder_count:
                parts.append(f"{reminder_count} напоминания")
            if list_count:
                parts.append(f"{list_count} списка")
            if event_count:
                parts.append(f"{event_count} события")
            if note_count:
                parts.append(f"{note_count} заметки")
            joined = ", ".join(parts) if parts else f"{len(result.items)} пунктов"
            return f"Разобрал это на {joined}. Выбери, как сохранить, если хочешь что-то поправить."

        item = result.items[0]
        if item.type == IntentType.REMINDER:
            if item.datetime and not item.date_only:
                when = item.datetime.strftime("%d.%m в %H:%M")
                return f"Понял, поставлю напоминание на {when}: {item.title}."
            if item.date_only or item.datetime is not None:
                return f"Понял, это напоминание про «{item.title}». Осталось выбрать удобное время."
            return f"Понял, это лучше сохранить как напоминание: {item.title}."
        if item.type == IntentType.EVENT:
            if item.datetime and not item.date_only:
                when = item.datetime.strftime("%d.%m в %H:%M")
                return f"Похоже, это событие «{item.title}» на {when}. Ниже можно сразу добавить напоминание."
            return f"Похоже, это событие «{item.title}». Дату понял, осталось уточнить время или просто сохранить."
        if item.type == IntentType.LIST:
            return f"Похоже, это список «{item.title}». Могу сразу сохранить его как список."
        if item.type == IntentType.NOTE:
            return f"Похоже, это заметка «{item.title}». Могу сохранить как есть или превратить в другой формат."
        return result.summary

