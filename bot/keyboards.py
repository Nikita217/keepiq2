from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.callbacks import InboxCallback


def mini_app_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Open KeepIQ", web_app=WebAppInfo(url=url))]]
    )


def mini_app_reply_keyboard(url: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Open KeepIQ", web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Send text, voice, links, screenshots...",
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
