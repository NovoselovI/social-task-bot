from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TASK_REWARD_FOR_WORKER

def trim_title(title: str, max_len: int = 25) -> str:
    if len(title) <= max_len:
        return title
    return title[:max_len - 3] + "..."

def tasks_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Доступные задания", callback_data="tasks_available")],

        [InlineKeyboardButton(text="✅ Добавить свое задание", callback_data="tasks_create")],
    ])


def task_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ YouTube", callback_data="task_type_youtube"),
        InlineKeyboardButton(text="📨 Telegram", callback_data="task_type_telegram")],
        [InlineKeyboardButton(text="🎵 TikTok", callback_data="task_type_tiktok"),InlineKeyboardButton(text="📸 Instagram", callback_data="task_type_instagram")
],
    ])




def open_link_kb(url: str, task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Открыть", url=url)
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Проверить выполнение",
                    callback_data=f"task_check_{task_id}"
                )
            ]
        ]
    )



def my_tasks_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Активные", callback_data="my_tasks_active")],
        [InlineKeyboardButton(text="✔️ Завершённые", callback_data="my_tasks_completed")],
        [InlineKeyboardButton(text="❌ Отменённые", callback_data="my_tasks_cancelled")],
    ])
def back_to_my_tasks_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data="tasks_my")]
    ])

def telegram_check_kb(username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Открыть канал",
                    url=f"https://t.me/{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Проверить подписку",
                    callback_data=f"check_tg_sub_{username}"
                )
            ]
        ]
    )

