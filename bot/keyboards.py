from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.callbacks import InboxCallback



def mini_app_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Open Mini App", web_app=WebAppInfo(url=url))]]
    )



def inbox_actions(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить",
                    callback_data=InboxCallback(action="confirm", item_id=item_id).pack(),
                ),
                InlineKeyboardButton(
                    text="Нужно ответить",
                    callback_data=InboxCallback(action="save_as", item_id=item_id, target="reply_later").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Как задачу",
                    callback_data=InboxCallback(action="save_as", item_id=item_id, target="task").pack(),
                ),
                InlineKeyboardButton(
                    text="Как заметку",
                    callback_data=InboxCallback(action="save_as", item_id=item_id, target="note").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Как список",
                    callback_data=InboxCallback(action="save_as", item_id=item_id, target="list").pack(),
                ),
                InlineKeyboardButton(
                    text="Как событие",
                    callback_data=InboxCallback(action="save_as", item_id=item_id, target="event").pack(),
                ),
            ],
        ]
    )
