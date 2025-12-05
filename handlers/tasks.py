import asyncio
import re
import aiohttp
import json
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


from states.task_states import CreateTaskState
from keyboards.tasks_kb import task_type_kb, tasks_menu_kb,open_link_kb,trim_title,my_tasks_menu_kb,back_to_my_tasks_kb,telegram_check_kb
from services.task_service import TasksService
from services.user_service import UserService
from config import TASK_PRICE_FOR_OWNER,TASK_REWARD_FOR_WORKER
from database.db import get_db


router = Router()



def extract_username_from_url(url: str):
    url = url.strip().replace('@', '').replace('https://', '').replace('http://', '')

    if "t.me/" in url:
        username = url.split("t.me/")[-1]
    else:
        username = url

    username = username.split("?")[0]
    username = username.split("/")[0]
    username = username.strip()


    username = ''.join(ch for ch in username if ch.isprintable())

    return username


async def bot_is_admin(bot, username: str):
    try:
        chat = await bot.get_chat(f"@{username}")
        member = await bot.get_chat_member(chat.id, bot.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print("ADMIN CHECK ERROR:", e)
        return False




@router.message(F.text == "🎯 Задания")
async def open_tasks_menu(message: types.Message):
    tg_id = message.from_user.id
    user = await UserService.get_user(message.from_user.id)
    if not user:
        await UserService.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            referrer_id=None
        )
        user = await UserService.get_user(message.from_user.id)

    if not user["phone"]:
        return await message.answer(
            "⚠️ Чтобы использовать раздел «Задания», подтвердите номер телефона.",
            parse_mode="HTML"
        )

    await message.answer(
        "<b>Раздел: Задания</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=tasks_menu_kb()
    )


@router.callback_query(F.data == "tasks_create")
async def tasks_create_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CreateTaskState.choosing_type)

    await callback.message.edit_text(
        "<b>Создание задания</b>\n\n"
        "Выберите тип задания:",
        reply_markup=task_type_kb(),
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(CreateTaskState.choosing_type, F.data.startswith("task_type_"))
async def choose_task_type(callback: types.CallbackQuery, state: FSMContext):
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
    await state.set_state(CreateTaskState.entering_url)

    await callback.message.edit_text(
        "Отправьте ссылку для задания.\n\n"
        "Например:\n"
        "• YouTube — ссылка на видео/канал\n"
        "• Telegram(бот должен быть добавлен как администратор!) — канал/пост\n"
        "• TikTok — видео/канал",
        parse_mode="HTML"
    )
    await callback.answer()



@router.message(CreateTaskState.entering_url)
async def enter_task_url(message: types.Message, state: FSMContext):
    url = message.text.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        return await message.answer("❌ Введите корректную ссылку (http/https).")


    data = await state.get_data()
    task_type = data["task_type"]


    if task_type == "telegram":
        chat_id = extract_username_from_url(url)

        if not chat_id:
            return await message.answer(
                "❌ Нельзя создать задание для приватного Telegram-канала.\n"
                "Используйте публичный канал с @username."
            )

        is_admin = await bot_is_admin(message.bot, chat_id)
        if not is_admin:
            return await message.answer(
                "❌ Бот НЕ является администратором канала.\n"
                "Добавьте бота как администратора."
            )

    await state.update_data(url=url)
    await state.set_state(CreateTaskState.entering_total_views)

    await message.answer(
        f"Сколько просмотров вы хотите купить?\n"
        f"Цена за 1 пользователя: <b>{TASK_PRICE_FOR_OWNER:.2f} SD</b>\n\n"
        f"Введите число:",
        parse_mode="HTML"
    )


@router.message(CreateTaskState.entering_total_views)
async def enter_task_total_views(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        return await message.answer("❌ Введите целое число.")

    total_views = int(text)
    if total_views <= 0:
        return await message.answer("❌ Количество должно быть > 0.")

    await state.update_data(total_views=total_views)

    await state.set_state(CreateTaskState.entering_title)

    await message.answer(
        "Введите название задания (максимум 150 символов)."
    )



@router.message(CreateTaskState.entering_title)
async def enter_task_title_and_create(message: types.Message, state: FSMContext):
    title = message.text.strip()


    if len(title) > 150:
        await message.answer(
            "❌ Название слишком длинное.\n"
            "Максимум: <b>150 символов</b>.\n\n"
            "Отправьте название снова:",
            parse_mode="HTML"
        )

        return

    if len(title) == 0:
        await message.answer(
            "❌ Название не может быть пустым.\n"
            "Отправьте название задания:",
            parse_mode="HTML"
        )
        return


    data = await state.get_data()
    task_type = data["task_type"]
    url = data["url"]
    total_views = data["total_views"]


    result = await TasksService.create_task_with_payment(
        tg_id=message.from_user.id,
        title=title,
        url=url,
        task_type=task_type,
        total_views=total_views,
    )

    if result["status"] == "user_not_found":
        await message.answer("❌ Пользователь не найден в базе. Попробуйте /start.")
        await state.clear()
        return

    if result["status"] == "insufficient_funds":
        need = result["need"]
        balance = result["balance"]
        await message.answer(
            "❌ Недостаточно средств для создания задания.\n\n"
            f"Нужно: <b>{need:.2f} SD</b>.\n"
            f"У вас на балансе: <b>{balance:.2f} SD</b>.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    cost = result["cost"]

    await message.answer(
        "<b>✅ Задание создано!</b>\n\n"
        f"<b>Название:</b> {title}\n"
        f"<b>Ссылка:</b> {url}\n"
        f"<b>Всего просмотров:</b> {total_views}\n"
        f"<b>Списано:</b> {cost:.2f} SD (по {TASK_PRICE_FOR_OWNER:.2f} SD за пользователя)",
        parse_mode="HTML",
        reply_markup=tasks_menu_kb()
    )

    await state.clear()


@router.callback_query(F.data == "tasks_available")
async def tasks_available(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    limit = 15
    offset = 0

    tasks = await TasksService.get_available_tasks_chunk(user_id, offset, limit)
    total = await TasksService.count_available_tasks(user_id)


    await callback.message.edit_text(
        "<b>📋 Доступные задания:</b>",
        parse_mode="HTML"
    )


    reward = 0.5

    kb = [
        [
            InlineKeyboardButton(
                text=f"▶ Смотреть рекламу {reward} SD",
                callback_data="ads_watch"
            )
        ]
    ]
    # -------------------------



    if tasks:
        for t in tasks:
            button_text = f"{trim_title(t['title'], 35)}  +{TASK_REWARD_FOR_WORKER:.2f}💰 ↗"
            kb.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"task_do_{t['id']}"
                )
            ])
    else:

        kb.append([
            InlineKeyboardButton(
                text="Нет доступных заданий",
                callback_data="none"
            )
        ])

    # кнопка "показать ещё"
    remaining = max(total - limit, 0)
    if remaining > 0:
        kb.append([
            InlineKeyboardButton(
                text=f"Показать ещё ({remaining})",
                callback_data=f"tasks_more_{limit}"
            )
        ])

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

    await callback.answer()





@router.callback_query(F.data.startswith("task_do_"))
async def task_do(callback: types.CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[-1])
    user_tg = callback.from_user.id

    task = await TasksService.get_task_by_id(task_id)
    if not task:
        return await callback.answer("Задание не найдено.", show_alert=True)

    if task["completed_views"] >= task["total_views"] or task["status"] != "active":
        return await callback.answer("Это задание уже завершено.", show_alert=True)

    url = task["url"]
    task_type = task["type"]
    is_admin_task = task["is_admin_task"] == 1


    await state.clear()


    await state.update_data(
        current_task_id=task_id,
        task_ready=False
    )


    if task_type == "telegram":
        username = extract_username_from_url(url)
        if not username:
            return await callback.answer("❌ Ошибка: канал не распознан.", show_alert=True)

        await state.update_data(tg_channel_username=username)


        asyncio.create_task(run_task_timer(state))

        await callback.message.answer(
            f"<b>{task['title']}</b>\n\n"
            f"Тип: Telegram\n"
            f"Канал: https://t.me/{username}\n\n"
            f"Награда: <b>{TASK_REWARD_FOR_WORKER:.2f} SD</b>\n\n"
            f"{'Это админское задание — подписка НЕ требуется.' if is_admin_task else 'После подписки нажмите «Проверить подписку».'}",
            parse_mode="HTML",
            reply_markup=telegram_check_kb(username)
        )
        await callback.answer()
        return


    await callback.message.answer(
        f"<b>{task['title']}</b>\n\n"
        f"Тип: <b>{task_type}</b>\n"
        f"Ссылка: <a href=\"{url}\">перейти</a>\n\n"
        f"Награда: <b>{TASK_REWARD_FOR_WORKER:.2f} SD</b>\n\n"
        f"<i>После просмотра нажмите «Проверить выполнение».</i>",
        parse_mode="HTML",
        reply_markup=open_link_kb(url, task_id),
        disable_web_page_preview=True
    )


    asyncio.create_task(run_task_timer(state))
    await callback.answer()



async def run_task_timer(state: FSMContext):

    await asyncio.sleep(15)
    await state.update_data(task_ready=True)

@router.callback_query(F.data.startswith("task_check_"))
async def task_check(callback: types.CallbackQuery, state: FSMContext):

    try:
        task_id = int(callback.data.split("_")[-1])
    except:
        return await callback.answer("Это старое сообщение. Откройте заново.", show_alert=True)

    user_id = callback.from_user.id
    data = await state.get_data() or {}

    # Проверяем что открытое задание = текущее
    if data.get("current_task_id") != task_id:
        return await callback.answer("Это старое сообщение. Откройте задание заново.", show_alert=True)

    # Проверяем таймер
    if not data.get("task_ready"):
        return await callback.answer("⏳ Подождите, задание ещё проверяется.", show_alert=True)

    # Проверяем само задание
    task = await TasksService.get_task_by_id(task_id)
    if not task or task["completed_views"] >= task["total_views"] or task["status"] != "active":
        await state.clear()
        return await callback.answer("Это задание уже завершено.", show_alert=True)

    # Выполняем задание — ТОЛЬКО finish_task
    result = await TasksService.finish_task(task_id, user_id)

    if result["status"] == "ok":
        try:
            await callback.message.edit_reply_markup(None)
        except:
            pass

        await callback.message.answer(
            f"🎉 <b>Задание выполнено!</b>\n"
            f"Вы получили: <b>{result['reward']} SD</b>",
            parse_mode="HTML"
        )

        await state.clear()
        return

    if result["status"] in ("already_completed", "limits_reached"):
        await state.clear()
        return await callback.answer("Это задание уже недоступно.", show_alert=True)

    if result["status"] == "no_user":
        await state.clear()
        return await callback.answer("Ошибка пользователя. Напишите /start.", show_alert=True)

    await state.clear()
    return await callback.answer("Ошибка выполнения, попробуйте позже.", show_alert=True)





async def complete_task(task_id: int, user_tg_id: int):
    db = await get_db()


    cur = await db.execute(
        "SELECT id, balance_sd FROM users WHERE tg_id = ?",
        (user_tg_id,)
    )
    user = await cur.fetchone()
    if not user:
        await db.close()
        return {"status": "no_user"}

    user_id = user["id"]


    cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = await cur.fetchone()
    if not task:
        await db.close()
        return {"status": "no_task"}


    if task["completed_views"] >= task["total_views"]:
        await db.close()
        return {"status": "limits_reached"}

    reward = TASK_REWARD_FOR_WORKER


    await db.execute(
        """
        UPDATE tasks 
        SET completed_views = completed_views + 1
        WHERE id = ?
        """,
        (task_id,)
    )


    new_balance = user["balance_sd"] + reward
    await db.execute(
        "UPDATE users SET balance_sd = ? WHERE id = ?",
        (new_balance, user_id)
    )


    now_ts = int(__import__("time").time())
    await db.execute(
        """
        INSERT INTO user_tasks (user_id, task_id, status, completed_at)
        VALUES (?, ?, 'completed', ?)
        """,
        (user_id, task_id, now_ts)
    )


    if task["completed_views"] + 1 >= task["total_views"]:
        await db.execute(
            "UPDATE tasks SET is_active = 0, status = 'finished' WHERE id = ?",
            (task_id,)
        )

    await db.commit()
    await db.close()

    return {
        "status": "ok",
        "reward": reward,
    }


@router.callback_query(F.data.startswith("tasks_more_"))
async def tasks_more(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    offset = int(callback.data.split("_")[-1])
    limit = 15

    tasks = await TasksService.get_available_tasks_chunk(user_id, offset, limit)
    total = await TasksService.count_available_tasks(user_id)

    if not tasks:
        await callback.answer("Больше нет.", show_alert=True)
        return

    remaining = max(total - (offset + limit), 0)


    kb = []

    for t in tasks:
        button_text = f"{trim_title(t['title'], 35)}  +{TASK_REWARD_FOR_WORKER:.2f}💰 ↗"
        kb.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"task_do_{t['id']}"
            )
        ])

    if remaining > 0:
        kb.append([
            InlineKeyboardButton(
                text=f"Показать ещё ({remaining})",
                callback_data=f"tasks_more_{offset + limit}"
            )
        ])

    await callback.message.edit_reply_markup(
        InlineKeyboardMarkup(inline_keyboard=kb)
    )

    await callback.answer()

@router.callback_query(F.data == "tasks_my")
async def open_my_tasks(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "<b>🧾 Мои задания</b>\n\nВыберите категорию:",
        parse_mode="HTML",
        reply_markup=my_tasks_menu_kb()
    )
    await callback.answer()



@router.callback_query(F.data.startswith("task_cancel_"))
async def cancel_user_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    user_tg = callback.from_user.id

    result = await TasksService.cancel_task(task_id, user_tg)

    if result["status"] == "ok":
        await callback.message.edit_text(
            f"❌ Задание отменено.\n"
            f"На ваш баланс возвращено: <b>{result['refund']:.2f} SD</b>",
            parse_mode="HTML"
        )
    elif result["status"] == "not_owner":
        await callback.answer("Вы не владелец этого задания.", show_alert=True)
    else:
        await callback.answer("Ошибка. Невозможно отменить.", show_alert=True)




async def send_task_cards(callback, user_tg, status, offset):
    tasks, total = await TasksService.get_my_tasks_by_status_paginated(
        owner_tg_id=user_tg,
        status=status,
        offset=offset,
        limit=5
    )


    if offset == 0 and not tasks:
        await callback.message.edit_text(
            {
                "active": "🟢 Активных заданий нет.",
                "finished": "✔️ Завершённых заданий нет.",
                "cancelled": "❌ Отменённых заданий нет."
            }[status],
            parse_mode="HTML",
            reply_markup=back_to_my_tasks_kb()
        )
        return


    headers = {
        "active": "🟢 Активные задания:",
        "finished": "✔️ Завершённые задания:",
        "cancelled": "❌ Отменённые задания:"
    }

    await callback.message.edit_text(
        f"<b>{headers[status]}</b>",
        parse_mode="HTML"
    )


    for t in tasks:
        text = (
            f"<b>{t['title']}</b>\n"
            f"Просмотры: {t['completed_views']} / {t['total_views']}\n"
        )

        if status == "active":
            text += (
                f"Статус: 🟢 Активно\n\n"
                "❗ При отмене возвращается <b>75%</b> от стоимости оставшихся просмотров."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"task_cancel_{t['id']}")]
            ])
        else:
            text += f"Статус: {'✔️ Завершено' if status=='finished' else '❌ Отменено'}"
            kb = None

        await callback.message.answer(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb
        )


    shown = offset + 5
    if shown < total:
        more_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Показать ещё ({total - shown})",
                callback_data=f"my_tasks_more_{status}_{shown}"
            )],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="tasks_my")]
        ])
    else:
        more_btn = back_to_my_tasks_kb()

    await callback.message.answer("·", reply_markup=more_btn)


@router.callback_query(F.data == "my_tasks_active")
async def show_active(callback: types.CallbackQuery):
    await send_task_cards(callback, callback.from_user.id, "active", 0)


@router.callback_query(F.data == "my_tasks_completed")
async def show_completed(callback: types.CallbackQuery):
    await send_task_cards(callback, callback.from_user.id, "finished", 0)


@router.callback_query(F.data == "my_tasks_cancelled")
async def show_cancelled(callback: types.CallbackQuery):
    await send_task_cards(callback, callback.from_user.id, "cancelled", 0)
@router.callback_query(F.data.startswith("my_tasks_more_"))
async def my_tasks_more(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    offset = int(parts[-1])
    status = parts[-2]

    offset = int(offset)

    await send_task_cards(callback, callback.from_user.id, status, offset)

@router.callback_query(F.data.startswith("check_tg_sub_"))
async def check_tg_sub(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bot = callback.bot

    data = await state.get_data()
    task_id = data.get("current_task_id")
    channel_username = data.get("tg_channel_username")

    if not task_id:
        return await callback.answer("Ошибка данных. Откройте задание заново.", show_alert=True)

    task = await TasksService.get_task_by_id(task_id)
    if not task:
        return await callback.answer("Задание недоступно.", show_alert=True)

    is_admin_task = task["is_admin_task"] == 1

    # 1) ЕСЛИ ЭТО АДМИНСКОЕ ТЕЛЕГРАМ ЗАДАНИЕ → НЕ ПРОВЕРЯЕМ ПОДПИСКУ
    if is_admin_task:

        data = await state.get_data() or {}

        if not data.get("task_ready"):
            return await callback.answer("⏳ Подождите, задание ещё не выполнено.", show_alert=True)

        result = await TasksService.finish_task(task_id, user_id)

        if result["status"] == "ok":
            try:
                await callback.message.edit_reply_markup(None)
            except:
                pass

            await callback.message.answer(
                f"🎉 <b>Задание выполнено!</b>\n"
                f"Вы получили: <b>{result['reward']} SD</b>",
                parse_mode="HTML"
            )
            await state.clear()
            return

        return await callback.answer("Ошибка выполнения.", show_alert=True)


    if not channel_username:
        return await callback.answer("Ошибка канала.", show_alert=True)

    try:
        chat = await bot.get_chat(f"@{channel_username}")
        member = await bot.get_chat_member(chat.id, user_id)

        if member.status not in ("member", "administrator", "creator"):
            return await callback.answer("❌ Вы не подписаны на канал.", show_alert=True)

    except Exception as e:
        print("CHECK TG ERROR:", e)
        return await callback.message.answer(
            "❌ <b>Невозможно проверить подписку.</b>\n"
            "Возможно, бот не админ в канале.",
            parse_mode="HTML"
        )

    # Подписка OK → завершаем
    result = await TasksService.finish_task(task_id, user_id)

    if result["status"] == "ok":
        try:
            await callback.message.edit_reply_markup(None)
        except:
            pass

        await callback.message.answer(
            f"🎉 Задание выполнено!\n"
            f"Вы получили: <b>{result['reward']} SD</b>",
            parse_mode="HTML"
        )

        await state.clear()
        return

    if result["status"] == "already_completed":
        await state.clear()
        return await callback.answer("Это задание уже выполнено.", show_alert=True)

    if result["status"] == "limits_reached":
        await state.clear()
        return await callback.answer("Задание закончено.", show_alert=True)

    return await callback.answer("Ошибка выполнения.", show_alert=True)



@router.callback_query(F.data == "ads_watch")
async def ads_watch(callback: types.CallbackQuery):
    user = callback.from_user

    payload = {
        "wid": "97390ede-3a34-4309-91ba-d1df213ed240",
        "language": user.language_code or "en",
        "isPremium": bool(user.is_premium),
        "firstName": user.first_name or "",
        "telegramId": str(user.id)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://bid.tgads.live/bot-request",
                json=payload
            ) as resp:
                text = await resp.text()
                print("ADEXIUM RAW RESPONSE:", text)

                if resp.status != 200:
                    return await callback.answer(
                        f"API Error: {resp.status}",
                        show_alert=True
                    )

                data = json.loads(text)

    except Exception as e:
        print("ADEXIUM REQUEST ERROR:", e)
        return await callback.answer(
            "Ошибка запроса к Adexium.",
            show_alert=True
        )

    # Если ответа нет
    if not isinstance(data, dict) or "image" not in data:
        return await callback.answer(
            "Рекламы сейчас нет, попробуйте позже.",
            show_alert=True
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=data.get("buttonText", "Перейти"),
                url=data["clickUrl"]
            ),
            InlineKeyboardButton(
                text="✔ Получил SD",
                callback_data="ads_reward"
            )
        ]
    ])

    await callback.message.answer_photo(
        photo=data["image"],
        caption=data.get("text", "Реклама"),
        reply_markup=kb
    )

    await callback.answer()

