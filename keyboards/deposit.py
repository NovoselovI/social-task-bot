from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def deposit_methods_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 TON (USDT)", callback_data="dep_method:ton"),InlineKeyboardButton(text="🔶 BEP20 (USDT)", callback_data="dep_method:bep20")],
        [InlineKeyboardButton(text="🇺🇦 Пополнение UAH", callback_data="dep_method:uah")]

    ])


def confirm_payment_kb(method: str, amount: float):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"dep_paid:{method}:{amount}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile_deposit")]
    ])
