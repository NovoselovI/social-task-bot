from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def bonus_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus"),InlineKeyboardButton(text="⚒ Майнеры", callback_data="miners_menu")],
         [InlineKeyboardButton(text="💎 Стейкинг", callback_data="bonus_staking")],
        [InlineKeyboardButton(text="🎟 Лотерея", callback_data="lottery_buy")]

    ])
