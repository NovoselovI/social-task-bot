from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def finance_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пополнения", callback_data="finance_deposits")],
        [InlineKeyboardButton(text="💸 Выводы", callback_data="finance_withdraws")]
    ])


def deposit_statuses_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ожидают", callback_data="dep_list:pending:0")],
        [InlineKeyboardButton(text="✅ Зачислены", callback_data="dep_list:approved:0")],
        [InlineKeyboardButton(text="❌ Отклонены", callback_data="dep_list:declined:0")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="finance_back_to_main")]
    ])


def deposits_list_kb(deposits, status: str, page: int, total_pages: int):
    rows = []

    for dep in deposits:
        dep_id = dep["id"]
        amount = dep["amount_usdt"]
        user_id = dep["user_id"]
        method = dep["method"].upper()

        text = f"#{dep_id} • {amount} USDT • {method} • {user_id}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"dep_view:{dep_id}:{status}:{page}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"dep_list:{status}:{page-1}"
        ))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"dep_list:{status}:{page+1}"
        ))

    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад к статусам",
            callback_data="finance_deposits"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def deposit_details_kb(dep_id: int, status: str, page: int):
    rows = []

    if status == "pending":
        rows.append([
            InlineKeyboardButton(
                text="✅ Зачислить",
                callback_data=f"dep_approve:{dep_id}:{status}:{page}"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"dep_decline:{dep_id}:{status}:{page}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад",
            callback_data=f"dep_list:{status}:{page}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def deposit_action_kb(dep_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Зачислить", callback_data=f"dep_approve:{dep_id}:notify:0")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"dep_decline:{dep_id}:notify:0")]
    ])


def withdraw_action_kb(wd_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Вывести",
                    callback_data=f"approve_wd:{wd_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отказать",
                    callback_data=f"decline_wd:{wd_id}"
                )
            ]
        ]
    )

def withdraw_statuses_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ожидают", callback_data="wd_list:pending:0")],
        [InlineKeyboardButton(text="✅ Выплачены", callback_data="wd_list:approved:0")],
        [InlineKeyboardButton(text="❌ Отклонены", callback_data="wd_list:declined:0")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="finance_back_to_main")]
    ])

def withdraws_list_kb(items, status: str, page: int, total_pages: int):
    rows = []

    for wd in items:
        wd_id = wd["id"]
        amount = wd["amount_usdt"]
        user_id = wd["user_id"]
        method = wd["method"].upper()

        text = f"#{wd_id} • {amount} USDT • {method} • {user_id}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"wd_view:{wd_id}:{status}:{page}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"wd_list:{status}:{page-1}"
        ))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"wd_list:{status}:{page+1}"
        ))
    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад к статусам",
            callback_data="finance_withdraws"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def withdraw_details_kb(wd_id: int, status: str, page: int):
    rows = []

    if status == "pending":
        rows.append([
            InlineKeyboardButton(
                text="✅ Выплатить",
                callback_data=f"wd_approve:{wd_id}:{status}:{page}"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"wd_decline:{wd_id}:{status}:{page}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="⬅ Назад",
            callback_data=f"wd_list:{status}:{page}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

