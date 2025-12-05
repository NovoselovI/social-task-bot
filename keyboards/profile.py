from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardMarkup, KeyboardButton


def phone_request_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def profile_kb(has_phone: bool):
    inline_kb = [
        [
            InlineKeyboardButton(text="💳 Пополнить", callback_data="profile_deposit"),
            InlineKeyboardButton(text="💸 Вывод", callback_data="profile_withdraw"),
        ],
        [
            InlineKeyboardButton(text="💱 Обмен", callback_data="exchange_menu"),
            InlineKeyboardButton(text="⚙ Настройки", callback_data="profile_settings"),
        ],
        [
            InlineKeyboardButton(text="🧾 Мои задания", callback_data="tasks_my")
        ],
        [
            InlineKeyboardButton(text="🎁 Ввести промокод", callback_data="enter_promo"),
        ],
        [
            InlineKeyboardButton(text="📢 Наш канал", url="https://t.me/SmartDollar_community"),
            InlineKeyboardButton(text="💬 Наш чат", url="https://t.me/smartdollarchat"),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb)


def profile_settings_kb(has_phone: bool):
    buttons = [
        [
            InlineKeyboardButton(text="📥 История пополнений", callback_data="hist_dep:0"),
            InlineKeyboardButton(text="📤 История выводов", callback_data="hist_wd:0"),
        ]
    ]

    if not has_phone:
        buttons.append([
            InlineKeyboardButton(text="📱 Подтвердить телефон", callback_data="confirm_phone")
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_profile")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)



def history_nav_kb(prefix: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []

    row = []

    if page > 0:
        row.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{prefix}:{page-1}"
            )
        )

    if page < total_pages - 1:
        row.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{prefix}:{page+1}"
            )
        )

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_profile"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
def exchange_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 SD → USDT", callback_data="convert_sd_usdt")
            ],
            [
                InlineKeyboardButton(text="🔄 USDT → SD", callback_data="convert_usdt_sd")
            ],
            [
                InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_profile")
            ]
        ]
    )