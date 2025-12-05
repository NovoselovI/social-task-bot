from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def staking_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Застейкать SD", callback_data="stake_add"),
        InlineKeyboardButton(text="📤 Вывести стейк", callback_data="stake_withdraw")],
        [InlineKeyboardButton(text="💰 Забрать награду", callback_data="stake_claim")],

    ])
