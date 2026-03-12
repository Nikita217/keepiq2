from aiogram.filters.callback_data import CallbackData


class InboxCallback(CallbackData, prefix="inbox"):
    action: str
    item_id: str
    target: str = ""
    value: str = ""
