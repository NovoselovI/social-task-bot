from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from services.task_service import TasksService
from database.db import get_db

from states.task_states import AdminCreateTaskState
from aiogram.fsm.context import FSMContext
from keyboards.tasks_kb import task_type_kb
router = Router()

@router.message(F.text == "/admin_tasks")
async def admin_tasks_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Активные задания", callback_data="admin_active_tasks_0")],
        [InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin_create_task_start")],
    ])

    await message.answer("<b>Админ панель заданий</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_create_task_start")
async def admin_create_task_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return

    await state.clear()
    await state.set_state(AdminCreateTaskState.choosing_type)

    await callback.message.edit_text(
        "<b>Создание админ-задания</b>\n\n"
        "Выберите тип задания:",
        reply_markup=task_type_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(AdminCreateTaskState.choosing_type, F.data.startswith("task_type_"))
async def admin_choose_task_type(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return

    data = callback.data
    type_key = data.replace("task_type_", "")

    type_map = {
        "youtube": "youtube",
        "telegram": "telegram",
        "tiktok": "tiktok",
        "instagram": "instagram",
    }
    task_type = type_map.get(type_key)

    if not task_type:
        await callback.answer("Неизвестный тип задания.", show_alert=True)
        return

    await state.update_data(task_type=task_type)
    await state.set_state(AdminCreateTaskState.entering_url)

    await callback.message.edit_text(
        "Отправьте ссылку для задания.\n\n"
        "• YouTube — видео/канал\n"
        "• Telegram — канал/пост\n"
        "• TikTok/Instagram — видео/пост",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminCreateTaskState.entering_url)
async def admin_enter_task_url(message: types.Message, state: FSMContext):
    url = message.text.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        return await message.answer("❌ Введите корректную ссылку (http/https).")

    await state.update_data(url=url)
    await state.set_state(AdminCreateTaskState.entering_total_views)

    await message.answer(
        "Сколько просмотров/выполнений должно быть у этого задания?\n\n"
        "Введите целое число:",
        parse_mode="HTML"
    )
@router.message(AdminCreateTaskState.entering_total_views)
async def admin_enter_total_views(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("❌ Введите целое число.")

    total_views = int(text)
    if total_views <= 0:
        return await message.answer("❌ Количество должно быть > 0.")

    await state.update_data(total_views=total_views)
    await state.set_state(AdminCreateTaskState.entering_title)

    await message.answer("Введите название задания (максимум 150 символов).")

@router.message(AdminCreateTaskState.entering_title)
async def admin_enter_title_and_create(message: types.Message, state: FSMContext):
    title = message.text.strip()

    if len(title) == 0:
        return await message.answer("❌ Название не может быть пустым. Введите ещё раз.")
    if len(title) > 150:
        return await message.answer("❌ Название слишком длинное (макс. 150 символов).")

    data = await state.get_data()
    task_type = data["task_type"]
    url = data["url"]
    total_views = data["total_views"]


    result = await TasksService.create_admin_task(
        title=title,
        url=url,
        task_type=task_type,
        total_views=total_views,
    )

    await message.answer(
        "<b>✅ Админ-задание создано!</b>\n\n"
        f"<b>Название:</b> {title}\n"
        f"<b>Ссылка:</b> {url}\n"
        f"<b>Всего выполнений:</b> {total_views}\n"
        f"<b>Тип:</b> {task_type}\n\n"
        "Оно уже доступно пользователям и отображается выше обычных заданий.",
        parse_mode="HTML"
    )

    await state.clear()



@router.callback_query(F.data.startswith("admin_active_tasks_"))
async def admin_show_active(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    parts = callback.data.split("_")
    offset = int(parts[-1])

    limit = 5
    tasks = await TasksService.get_active_tasks_admin(offset, limit)
    total = await TasksService.count_active_tasks_admin()

    if not tasks:
        await callback.answer("Нет активных заданий", show_alert=True)
        return

    kb = []

    for t in tasks:
        title_short = t["title"][:35] + "..." if len(t["title"]) > 35 else t["title"]
        kb.append([
            InlineKeyboardButton(
                text=f"{title_short} ({t['completed_views']}/{t['total_views']})",
                callback_data=f"admin_task_{t['id']}"
            )
        ])

    remaining = total - (offset + limit)
    if remaining > 0:
        kb.append([
            InlineKeyboardButton(
                text=f"Показать ещё ({remaining})",
                callback_data=f"admin_active_tasks_{offset + limit}"
            )
        ])

    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_active_tasks_0")])

    await callback.message.edit_text(
        "<b>Активные задания:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data.startswith("admin_task_"))
async def admin_open_task(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    task_id = int(callback.data.split("_")[-1])
    task = await TasksService.get_task_by_id(task_id)

    if not task:
        await callback.answer("Задание не найдено", show_alert=True)
        return

    owner = await TasksService.get_user_by_id(task["owner_id"])
    if task["is_admin_task"] == 1 or task["owner_id"] is None:
       owner_text = "👤 Автор: <b>Администратор</b>\n"
       kb = InlineKeyboardMarkup(inline_keyboard=[
           [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_task_{task['id']}")],
           [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_active_tasks_0")]
       ])
       await callback.message.edit_text(owner_text , parse_mode="HTML", reply_markup=kb)
       await callback.answer()
    else:
        owner = await TasksService.get_user_by_id(task["owner_id"])

    text = (
        f"<b>Задание #{task['id']}</b>\n\n"
        f"📌 <b>{task['title']}</b>\n"
        f"👤 Автор: @{owner['username']} (ID {owner['tg_id']})\n"
        f"🔗 Ссылка: {task['url']}\n\n"
        f"🧮 Выполнено: {task['completed_views']}/{task['total_views']}\n"
        f"💵 Цена для автора: {task['reward_sd']} SD\n"
        f"📅 Создано: {task['created_at']}\n"
        f"🟩 Статус: {task['status']}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Отменить с возвратом 75%", callback_data=f"admin_cancel_refund_{task_id}")],
        [InlineKeyboardButton(text="❌ Удалить без возврата", callback_data=f"admin_cancel_norefund_{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_active_tasks_0")]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cancel_refund_"))
async def admin_cancel_with_refund(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    task_id = int(callback.data.split("_")[-1])
    result = await TasksService.admin_cancel_task(task_id, refund=True)

    await callback.message.edit_text(
        f"Задание #{task_id} отменено.\n"
        f"Возврат 75% выполнен.",
        parse_mode="HTML"
    )

    # уведомление автора
    user_id = result["user_tg_id"]
    await callback.bot.send_message(
        chat_id=user_id,
        text="⚠️ Одно из ваших заданий было отменено администратором. 75% средств возвращено."
    )

    await callback.answer()

@router.callback_query(F.data.startswith("admin_cancel_norefund_"))
async def admin_cancel_no_refund(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    task_id = int(callback.data.split("_")[-1])
    result = await TasksService.admin_cancel_task(task_id, refund=False)

    await callback.message.edit_text(
        f"Задание #{task_id} удалено без возврата средств.",
        parse_mode="HTML"
    )

    # уведомление автора
    user_id = result["user_tg_id"]
    await callback.bot.send_message(
        chat_id=user_id,
        text="⚠️ Одно из ваших заданий было удалено администратором за нарушение правил."
    )

    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_task_"))
async def admin_delete_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[-1])

    task = await TasksService.get_task_by_id(task_id)
    if not task:
        return await callback.answer("Задание не найдено.", show_alert=True)


    if task["is_admin_task"] == 1:
        db = await get_db()
        await db.execute(
            "UPDATE tasks SET is_active = 0, status = 'cancelled' WHERE id = ?",
            (task_id,)
        )
        await db.commit()
        await db.close()

        await callback.message.answer(
            f"🗑 Админское задание <b>ID {task_id}</b> удалено.",
            parse_mode="HTML"
        )
        return


    result = await TasksService.admin_cancel_task(task_id, refund=False)

    await callback.message.answer(
        f"🗑 Задание <b>ID {task_id}</b> удалено.",
        parse_mode="HTML"
    )
