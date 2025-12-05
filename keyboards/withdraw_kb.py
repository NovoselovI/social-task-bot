from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def withdraw_methods_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔵 TON USDT", callback_data="wd_method:ton")
            ],
            [
                InlineKeyboardButton(text="🟧 BEP20 USDT", callback_data="wd_method:bep20")
            ]
        ]
    )
