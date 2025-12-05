from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_user_kb(tg_id: int, inviter_id: int = None):

    rows = []


    ref_row = [
        InlineKeyboardButton(text="👥 Рефералы", callback_data=f"user_refs:{tg_id}")
    ]

    if inviter_id:
        ref_row.append(
            InlineKeyboardButton(
                text="👤 Пригласивший",
                callback_data=f"user_profile:{inviter_id}"
            )
        )
    else:

        ref_row.append(
            InlineKeyboardButton(text=" ", callback_data="ignore")
        )

    rows.append(ref_row)


    rows.append([
        InlineKeyboardButton(text="💳 Пополнения", callback_data=f"user_deposits:{tg_id}"),
        InlineKeyboardButton(text="💸 Выводы", callback_data=f"user_withdraws:{tg_id}")
    ])


    rows.append([
        InlineKeyboardButton(text="🚫 Забанить", callback_data=f"user_ban:{tg_id}"),
        InlineKeyboardButton(text="🔓 Разбанить", callback_data=f"user_unban:{tg_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
