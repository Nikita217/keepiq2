from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo

from bot.callbacks import InboxCallback

INLINE_OPEN_TEXT = "Открыть KeepIQ"
MENU_OPEN_TEXT = "KeepIQ"


def mini_app_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=INLINE_OPEN_TEXT, web_app=WebAppInfo(url=url))]]
    )


def mini_app_menu_button(url: str) -> MenuButtonWebApp:
    return MenuButtonWebApp(text=MENU_OPEN_TEXT, web_app=WebAppInfo(url=url))


def inbox_actions(item_id: str, suggested_actions: list[dict] | None = None) -> InlineKeyboardMarkup:
    actions = suggested_actions or []
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []

    for index, action in enumerate(actions[:4]):
        current_row.append(
            InlineKeyboardButton(
                text=action.get("label", "Выбрать"),
                callback_data=InboxCallback(action="suggest", item_id=item_id, value=str(index)).pack(),
            )
        )
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    if not rows:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Сохранить",
                    callback_data=InboxCallback(action="confirm", item_id=item_id).pack(),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
