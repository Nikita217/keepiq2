from __future__ import annotations

from collections import Counter

from domain.enums import IntentType
from domain.models import StructuredAnalysisResult


class UserReplyFormatter:
    def format(self, result: StructuredAnalysisResult) -> str:
        if result.should_go_to_inbox:
            return "Я сохранил это во входящие, чтобы не потерять. Можешь потом выбрать, как лучше оформить."
        if not result.items:
            return result.summary
        if len(result.items) > 1:
            counts = Counter(item.type.value for item in result.items)
            pieces = []
            if counts.get(IntentType.TASK.value):
                pieces.append(f"{counts[IntentType.TASK.value]} задачи")
            if counts.get(IntentType.NOTE.value):
                pieces.append(f"{counts[IntentType.NOTE.value]} идеи")
            if counts.get(IntentType.REPLY_LATER.value):
                pieces.append(f"{counts[IntentType.REPLY_LATER.value]} сообщения на ответ")
            joined = " и ".join(pieces) if pieces else f"{len(result.items)} объектов"
            if result.source_type.value == "voice_message":
                return f"Я нашел в голосовом {joined}."
            return f"Я нашел здесь {joined}."

        item = result.items[0]
        if item.type == IntentType.TASK:
            return f"Похоже, это задача: {item.title}. Когда напомнить?"
        if item.type == IntentType.EVENT:
            return f"Похоже, это событие: {item.title}. Поставить напоминание?"
        if item.type == IntentType.LIST:
            return f"Похоже, это список: {item.title}."
        if item.type == IntentType.REPLY_LATER:
            return "Похоже, к этому сообщению лучше вернуться позже."
        if item.type == IntentType.NOTE:
            return f"Похоже, это заметка: {item.title}."
        if item.type == IntentType.SAVE_ONLY:
            return "Похоже, это лучше просто сохранить без лишних действий."
        return result.summary

