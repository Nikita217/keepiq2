from __future__ import annotations

TICKET_KEYWORDS = [
    "билет",
    "ticket",
    "рейс",
    "flight",
    "seat",
    "concert",
    "бронь",
    "booking",
    "reservation",
    "check-in",
    "регистрация",
    "заказ",
]



def looks_like_ticket(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in TICKET_KEYWORDS)
