

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎯 Задания"),
            KeyboardButton(text="👤 Профиль")
        ],
        [
            KeyboardButton(text="🤝 Пригласить друга"),
            KeyboardButton(text="🎁 Бонусы")
        ],
        [
            KeyboardButton(text="🛠️ Тех. поддержка")
        ]
    ],
    resize_keyboard=True
)
