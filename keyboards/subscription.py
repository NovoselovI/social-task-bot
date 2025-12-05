from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def subscription_kb(channels: list[str]):

    rows = []

    # Кнопки каналов
    for username in channels:
        rows.append([
            InlineKeyboardButton(
                text=f"📢 @{username}",
                url=f"https://t.me/{username}"
            )
        ])


    rows.append([
        InlineKeyboardButton(
            text="🔄 Проверить подписку",
            callback_data="check_subs"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
