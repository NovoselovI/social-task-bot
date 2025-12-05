import random

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.admin_menu_text  import build_user_profile_text

from services.user_service import UserService
from services.referrals_service import ReferralsService
from services.withdraw_service import WithdrawService
from services.deposit_service import DepositService
from services.tech_service import TechService

from handlers.restrictred import pretty_date
from keyboards.admin_user import admin_user_kb
from config import ADMINS

from database.db import get_db
import time


router = Router()

ITEMS_PER_PAGE = 20

class BotSettingsState(StatesGroup):
    ton_address = State()
    bep20_address = State()
    uah_requisites = State()
    min_withdraw = State()


class RefRewardState(StatesGroup):
    waiting_for_value = State()


class ChannelSettingsState(StatesGroup):
    add = State()
    delete = State()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ У вас нет доступа.")
    maintenance = await TechService.get_mode()
    status_text = "🔴 Увімкнено" if maintenance else "🟢 Вимкнено"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🛠 Технічні роботи: {status_text}",
                callback_data="toggle_maintenance"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🏷Промокоды",
                callback_data="admin_promocodes"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙ Настройки бота",
                callback_data="bot_settings"
            )
        ],

    ])

    await message.answer(
        text=(
             "🔐 <b>Админ-панель</b>\n\n"
    "Краткая навигация по возможностям:\n\n"

    "👥 <b>Пользователи</b>\n"
    "• /user ID или @username — профиль, балансы, рефералы, бан/разбан.\n\n"

    "🧾 <b>Задания</b>\n"
    "• /admin_tasks — просмотр, управление, удаление и отмена заданий.\n\n"

    "💸 <b>Финансы</b>\n"
    "• /finance — статистика депозитов, выводов и общего баланса системы.\n\n"

    "📣 <b>Рассылка</b>\n"
    "• /broadcast — массовые рассылки, фото+текст, ЛС по ID.\n\n"

    "🎟 <b>Лотерея</b>\n"
    "• /lotery— управление билетами, результатами и розыгрышами.\n\n"

    "📊 <b>Статистика</b>\n"
    "• /stats — новые пользователи, выполненные задания, активность.\n\n"

    "🛠 <b>Технические работы</b>\n"
    "Используйте кнопку ниже для включения/выключения режима."
        ),
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(Command("user"))
async def admin_get_user(message: types.Message):
    args = message.text.split()

    if len(args) < 2:
        return await message.answer("Введите ID или @username:\nПример: <code>/user 123456</code>")

    query = args[1]


    if query.isdigit():
        user = await UserService.get_user(int(query))
    else:

        user = await UserService.get_user_by_username(query.replace("@", ""))

    if not user:
        return await message.answer("❌ Пользователь не найден.")

    tg_id = user["tg_id"]
    refs_count = await ReferralsService.count_referrals(tg_id)

    text = await build_user_profile_text(user)

    return await message.answer(
        text,
        reply_markup=admin_user_kb(tg_id, inviter_id=user["referrer_id"]),
        parse_mode="HTML"
    )



@router.callback_query(lambda c: c.data.startswith("user_refs:"))
async def show_user_refs(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    parent_tg_id = int(callback.data.split(":")[1])

    parent_user = await UserService.get_user(parent_tg_id)
    if not parent_user:
        return await callback.answer("Пользователь не найден", show_alert=True)

    refs = await ReferralsService.get_referrals(parent_tg_id)


    if not refs:
        return await callback.answer(
            "У этого пользователя нет рефералов.",
            show_alert=True
        )

    lines = []
    buttons = []



    for r in refs:
        tg_id = r["tg_id"]
        username = r["username"]
        first_name = r["first_name"] or "Без имени"

        uname = f"@{username}" if username else "—"

        lines.append(f"▫️ <b>{first_name}</b> ({uname}) — <code>{tg_id}</code>")

        buttons.append([
            InlineKeyboardButton(
                text=f"{first_name} ({tg_id})",
                callback_data=f"user_profile:{tg_id}"
            )
        ])


    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"user_profile:{parent_tg_id}"
        )
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return await callback.message.edit_text(
        f"👥 <b>Рефералы пользователя {parent_tg_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n" +
        "\n".join(lines),
        reply_markup=kb
    )



@router.callback_query(lambda c: c.data.startswith("user_profile:"))
async def admin_user_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = int(callback.data.split(":")[1])

    user = await UserService.get_user(tg_id)
    if not user:
        return await callback.answer("Пользователь не найден", show_alert=True)

    refs_count = await ReferralsService.count_referrals(tg_id)

    text = await build_user_profile_text(user)

    return await callback.message.edit_text(
        text,
        reply_markup=admin_user_kb(tg_id, inviter_id=user["referrer_id"])
    )

@router.callback_query(lambda c: c.data.startswith("user_ban:"))
async def admin_ban_user(callback: types.CallbackQuery):
    tg_id = int(callback.data.split(":")[1])


    await UserService.ban_user(tg_id)

    user = await UserService.get_user(tg_id)
    text = await build_user_profile_text(user)

    await callback.message.edit_text(
        text, reply_markup=admin_user_kb(tg_id, inviter_id=user["referrer_id"])
    )
    await callback.answer("Пользователь забанен")

@router.callback_query(lambda c: c.data.startswith("user_unban:"))
async def admin_unban_user(callback: types.CallbackQuery):
    tg_id = int(callback.data.split(":")[1])


    await UserService.unban_user(tg_id)

    user = await UserService.get_user(tg_id)

    text = await build_user_profile_text(user)

    await callback.message.edit_text(
        text,
        reply_markup=admin_user_kb(tg_id, inviter_id=user["referrer_id"])
    )
    await callback.answer("Пользователь разбанен")

@router.callback_query(F.data.startswith("user_deposits:"))
async def admin_user_deposits(callback: types.CallbackQuery):
    tg_id = int(callback.data.split(":")[1])

    deps = await DepositService.get_by_status("approved")
    deps = [d for d in deps if d["user_id"] == tg_id]

    if not deps:
        return await callback.answer("У пользователя нет пополнений.", show_alert=True)

    text = f"💳 <b>Пополнения пользователя {tg_id}</b>\n━━━━━━━━━━━━━━\n"

    for d in deps[:20]:
        text += (
            f"ID: {d['id']}\n"
            f"Сумма: {d['amount_usdt']} USDT\n"
            f"Метод: {d['method']}\n"
            f"Дата: {pretty_date(d['created_at'])}\n"
            "----------------------\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data.startswith("user_withdraws:"))
async def admin_user_withdraws(callback: types.CallbackQuery):
    tg_id = int(callback.data.split(":")[1])

    wds = await WithdrawService.get_by_status("approved")
    wds = [w for w in wds if w["user_id"] == tg_id]

    if not wds:
        return await callback.answer("У пользователя нет выводов.", show_alert=True)

    text = f"💸 <b>Выводы пользователя {tg_id}</b>\n━━━━━━━━━━━━━━\n"

    for w in wds[:20]:
        text += (
            f"ID: {w['id']}\n"
            f"Сумма: {w['amount_usdt']} USDT\n"
            f"Метод: {w['method']}\n"
            f"Кошелёк: {w['wallet']}\n"
            f"Дата: {pretty_date(w['created_at'])}\n"
            "----------------------\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()

@router.callback_query(F.data == "toggle_maintenance")
async def toggle_maintenance(callback: types.CallbackQuery):


    current = await TechService.get_mode()
    new_state = not current

    await TechService.set_mode(new_state)

    text = (
        "🔴 Технічні роботи <b>увімкнено</b>."
        if new_state else
        "🟢 Технічні роботи <b>вимкнено</b>."
    )

    await callback.message.edit_text(
        text + "\n\nПоверніться в адмінку → /admin",
        parse_mode="HTML"
    )

    await callback.answer()

def broadcast_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 Массовая рассылка (текст)", callback_data="bc_text")],
        [InlineKeyboardButton(text="🖼 Массовая рассылка (фото+текст)", callback_data="bc_photo")],
        [InlineKeyboardButton(text="📬 Личная рассылка по ID", callback_data="bc_personal")],
    ])

@router.message(F.text == "/broadcast")
async def broadcast_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "<b>Меню рассылки</b>\nВыберите тип рассылки:",
        reply_markup=broadcast_menu(),
        parse_mode="HTML"
    )
@router.callback_query(F.data == "bot_settings")
async def open_bot_settings(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Награда за реферала", callback_data="change_ref_reward")],
        [
            InlineKeyboardButton(text="💎 TON адрес", callback_data="set_ton_address"),
            InlineKeyboardButton(text="🔶 BEP20 адрес", callback_data="set_bep20_address")
        ],
        [
            InlineKeyboardButton(text="🇺🇦 UAH реквизиты", callback_data="set_uah_requisites"),
            InlineKeyboardButton(text="📉 Минимальная сумма вывода", callback_data="set_min_withdraw")
        ],
        [InlineKeyboardButton(text="📢 Обязательные каналы", callback_data="req_channels")]

    ])

    await callback.message.edit_text(
        "⚙ <b>Настройки бота</b>\nВыберите параметр:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_ref_reward")
async def ask_new_ref_reward(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Введите новую награду за реферала (SD):")
    await state.set_state(RefRewardState.waiting_for_value)
    await callback.answer()


@router.message(RefRewardState.waiting_for_value)
async def save_new_ref_reward(message: types.Message, state: FSMContext):
    value = message.text.strip()

    try:
        value = float(value)
    except:
        return await message.answer("❌ Введите число")

    from services.ref_reward_service import RefRewardService
    await RefRewardService.set_reward(value)

    await message.answer(f"✔ Награда за реферала обновлена: {value} SD")
    await state.clear()

@router.callback_query(F.data == "set_ton_address")
async def set_ton_address(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsState.ton_address)
    await callback.message.edit_text("Введите новый TON-адрес:")
    await callback.answer()

@router.message(BotSettingsState.ton_address)
async def save_ton_address(message: types.Message, state: FSMContext):
    await DepositService.set_setting("TON_ADDRESS", message.text.strip())
    await message.answer("✔ TON-адрес обновлён.")
    await state.clear()
@router.callback_query(F.data == "set_bep20_address")
async def set_bep20_address(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsState.bep20_address)
    await callback.message.edit_text("Введите новый BEP20 адрес (USDT):")
    await callback.answer()

@router.message(BotSettingsState.bep20_address)
async def save_bep20_address(message: types.Message, state: FSMContext):
    await DepositService.set_setting("BEP20_ADDRESS", message.text.strip())
    await message.answer("✔ BEP20 адрес обновлён.")
    await state.clear()
@router.callback_query(F.data == "set_uah_requisites")
async def set_uah_requisites(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsState.uah_requisites)
    await callback.message.edit_text("Введите новые UAH реквизиты (можно многострочно):")
    await callback.answer()

@router.message(BotSettingsState.uah_requisites)
async def save_uah_requisites(message: types.Message, state: FSMContext):
    await DepositService.set_setting("UAH_REQUISITES", message.text)
    await message.answer("✔ UAH реквизиты обновлены.")
    await state.clear()


@router.callback_query(F.data == "set_min_withdraw")
async def set_min_withdraw(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotSettingsState.min_withdraw)
    await callback.message.edit_text("Введите минимальную сумму вывода (USDT):")
    await callback.answer()


@router.message(BotSettingsState.min_withdraw)
async def save_min_withdraw(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
    except:
        return await message.answer("❌ Введите число.")

    await DepositService.set_setting("MIN_WITHDRAW", value)
    await message.answer(f"✔ Минимальный вывод обновлён: {value} USDT")
    await state.clear()


@router.message(Command("stats"))
async def admin_stats(message: types.Message):

    now = int(time.time())
    ts_24h = now - 86400
    ts_30d = now - 86400 * 30

    db = await get_db()


    cur = await db.execute("SELECT COUNT(*) as c FROM users WHERE reg_date >= DATETIME('now','-1 day')")
    new_24h = await cur.fetchone()

    cur = await db.execute("SELECT COUNT(*) as c FROM users WHERE reg_date >= DATETIME('now','-30 day')")
    new_30d = await cur.fetchone()

    cur = await db.execute("SELECT COUNT(*) as c FROM users")
    total_users = await cur.fetchone()



    cur = await db.execute(
        "SELECT SUM(reward_sd) as s FROM user_tasks "
        "WHERE status='completed' AND completed_at >= ?", (ts_24h,)
    )
    earn_24h = await cur.fetchone()

    cur = await db.execute(
        "SELECT SUM(reward_sd) as s FROM user_tasks "
        "WHERE status='completed' AND completed_at >= ?", (ts_30d,)
    )
    earn_30d = await cur.fetchone()

    cur = await db.execute(
        "SELECT SUM(reward_sd) as s FROM user_tasks WHERE status='completed'"
    )
    earn_all = await cur.fetchone()


    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE viewed_at >= ?", (ts_24h,)
    )
    views_24h = await cur.fetchone()

    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE viewed_at >= ?", (ts_30d,)
    )
    views_30d = await cur.fetchone()

    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE viewed_at IS NOT NULL"
    )
    views_all = await cur.fetchone()


    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE status='completed' AND completed_at >= ?",
        (ts_24h,)
    )
    comp_24h = await cur.fetchone()

    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE status='completed' AND completed_at >= ?",
        (ts_30d,)
    )
    comp_30d = await cur.fetchone()

    cur = await db.execute(
        "SELECT COUNT(*) as c FROM user_tasks WHERE status='completed'"
    )
    comp_all = await cur.fetchone()

    await db.close()


    text = (
        "<b>📊 Статистика бота</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>👤 Пользователи</b>\n"
        f"• Новых за 24ч: <b>{new_24h['c']}</b>\n"
        f"• Новых за 30д: <b>{new_30d['c']}</b>\n"
        f"• Всего: <b>{total_users['c']}</b>\n\n"

        "<b>💰 Заработано SD пользователями</b>\n"
        f"• За 24ч: <b>{earn_24h['s'] or 0:.2f}</b> SD\n"
        f"• За 30д: <b>{earn_30d['s'] or 0:.2f}</b> SD\n"
        f"• Всего: <b>{earn_all['s'] or 0:.2f}</b> SD\n\n"

        "<b>👀 Просмотры заданий</b>\n"
        f"• За 24ч: <b>{views_24h['c']}</b>\n"
        f"• За 30д: <b>{views_30d['c']}</b>\n"
        f"• Всего: <b>{views_all['c']}</b>\n\n"

        "<b>🎯 Выполненные задания</b>\n"
        f"• За 24ч: <b>{comp_24h['c']}</b>\n"
        f"• За 30д: <b>{comp_30d['c']}</b>\n"
        f"• Всего: <b>{comp_all['c']}</b>\n"
    )

    await message.answer(text, parse_mode="HTML")

@router.message(Command("lotery"))
async def admin_run_lottery(message: types.Message):
    from config import ADMINS
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ У вас нет доступа.")

    db = await get_db()


    cur = await db.execute("SELECT user_id FROM lottery_tickets")
    tickets = await cur.fetchall()

    if not tickets:
        await message.answer("🎟 Лотерея не может быть проведена — нет ни одного билета.")
        await db.close()
        return


    users = list({row["user_id"] for row in tickets})

    if len(users) < 5:
        await message.answer("❌ Нужно минимум 5 участников для розыгрыша.")
        await db.close()
        return

    random.shuffle(users)

    winners = users[:5]
    percents = [45, 25, 10, 5, 5]


    total_fund = len(tickets) * 10

    text = "🏆 <b>Результаты лотереи</b>\n━━━━━━━━━━━━━━\n"
    now = int(time.time())

    for place, user_id in enumerate(winners, start=1):
        percent = percents[place - 1]
        prize = total_fund * percent / 100


        await db.execute(
            "INSERT INTO lottery_results (user_id, place, prize_sd, created_at) VALUES (?, ?, ?, ?)",
            (user_id, place, prize, now)
        )


        await UserService.increment_balance_sd(user_id, prize)

        text += f"{place}) <code>{user_id}</code> — <b>{prize:.2f} SD</b>\n"


        try:
            await message.bot.send_message(
                user_id,
                f"🎉 Вы выиграли в лотерее!\n🏅 Место: {place}\n💰 Приз: <b>{prize:.2f} SD</b>",
                parse_mode="HTML"
            )
        except:
            pass

    # полностью очищаем билеты
    await db.execute("DELETE FROM lottery_tickets")
    await db.commit()
    await db.close()

    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "req_channels")
async def open_req_channels_menu(cb: types.CallbackQuery):
    db = await get_db()
    cur = await db.execute("SELECT channel_id, username, title FROM required_channels")
    rows = await cur.fetchall()
    await db.close()

    if not rows:
        text = "📢 Обязательных каналов пока нет."
    else:
        text = "<b>📢 Обязательные каналы:</b>\n\n"
        for ch in rows:
            text += f"• <b>{ch['title']}</b> — @{ch['username']} — <code>{ch['channel_id']}</code>\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="req_ch_add")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="req_ch_delete")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_back")]
    ])

    await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cb.answer()

@router.callback_query(F.data == "req_ch_add")
async def req_ch_add_start(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChannelSettingsState.add)

    await cb.message.answer(
        "Введите данные канала в формате:\n\n"
        "<code>ID username Название</code>\n\n"
        "Пример:\n<code>-1001234567890 mychannel Наш канал</code>",
        parse_mode="HTML"
    )
    await cb.answer()

@router.message(ChannelSettingsState.add)

async def req_ch_add_save(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split(" ", 2)
        channel_id = int(parts[0])
        username = parts[1]
        title = parts[2]
    except:
        return await message.answer(
            "❌ Неверный формат.\nПример:\n<code>-1001234567890 mychannel Наш канал</code>",
            parse_mode="HTML"
        )

    db = await get_db()
    await db.execute(
        """
        INSERT OR IGNORE INTO required_channels (channel_id, username, title)
        VALUES (?, ?, ?)
        """,
        (channel_id, username, title)
    )
    await db.commit()
    await db.close()

    await state.clear()
    await message.answer("✔ Канал добавлен!\nКоманда: /admin")

@router.callback_query(F.data == "req_ch_delete")
async def req_ch_delete_menu(cb: types.CallbackQuery):
    db = await get_db()
    cur = await db.execute("SELECT channel_id, title FROM required_channels")
    rows = await cur.fetchall()
    await db.close()

    if not rows:
        await cb.answer("Список пуст.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {r['title']}", callback_data=f"req_ch_del_{r['channel_id']}")]
        for r in rows
    ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="req_channels")]])

    await cb.message.edit_text("Выберите канал для удаления:", reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("req_ch_del_"))
async def req_ch_delete_do(cb: types.CallbackQuery):
    channel_id = int(cb.data.split("_")[-1])

    db = await get_db()
    await db.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    await db.commit()
    await db.close()

    await cb.answer("Удалено!")
    await cb.message.answer("✔ Канал удалён.\nКоманда: /admin")

