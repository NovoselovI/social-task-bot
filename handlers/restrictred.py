from aiogram import Router, types, F
from aiogram.filters import Command
from datetime import datetime
from database.db import get_db
import random,time

from states.phone_state import PhoneState


from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states.converting_states import ConvertSD, ConvertUSDT

from services.miner_service import MinerService
from services.promocode_service import PromoCodeService
from services.user_service import UserService
from services.withdraw_service import WithdrawService
from services.deposit_service import DepositService
from services.referrals_service import ReferralsService
from services.bonus_service import BonusService
from services.staking_service import StakingService
from services.task_service import TasksService


from keyboards.main_menu import main_menu

from keyboards.profile import profile_kb,history_nav_kb,exchange_menu_kb,phone_request_kb,profile_settings_kb
from keyboards.bonus import bonus_menu_kb

from config import SUPPORT_USERNAME
router = Router()
ALLOWED_PREFIXES = (
    "+380",  # Украина
    "+7",    # Россия + Казахстан
    "+375",  # Беларусь
    "+374",  # Армения
    "+994",  # Азербайджан
    "+373",  # Молдова
    "+992",  # Таджикистан
    "+996",  # Кыргызстан
    "+48",   # Польша
)

ITEMS_PER_PAGE = 5
BASE_PERCENT = 0.25
REF_PERCENT = 0.01

class PromoState(StatesGroup):
    waiting_code = State()


@router.message(Command("menu"))
async def menu_cmd(message: types.Message, state: FSMContext):
    await state.clear()



    await message.answer(
        "🎉 Добро пожаловать в меню!\n"
        "Вы успешно прошли проверку подписки.",
        reply_markup=main_menu

    )


def pretty_date(date_str: str):
    if not date_str:
        return "—"
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%d.%m.%Y %H:%M")


@router.message(F.text == "👤 Профиль")
async def profile_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id


    user = await UserService.get_user(tg_id)
    if not user:
        return await message.answer("Ошибка: пользователь не найден!")


    stake = await StakingService.get_user(tg_id)
    stake_amount = stake["stake_amount"] or 0
    stake_earned = stake["stake_earned"] or 0


    ref_count = await ReferralsService.count_referrals(tg_id)
    percent = BASE_PERCENT + ref_count * REF_PERCENT
    daily_income = stake_amount * percent / 100


    earnings = await TasksService.get_user_earnings(tg_id)


    referrer_tg = "—"
    if user["referrer_id"]:
        ref_user = await UserService.get_user_by_id(user["referrer_id"])
        referrer_tg = ref_user["tg_id"] if ref_user else "—"


    has_phone = bool(user["phone"])


    from keyboards.profile import profile_kb
    kb = profile_kb(has_phone)


    text = (
        f"👤 <b>Мой профиль</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 TG ID: <code>{user['tg_id']}</code>\n"
        f"💬 Username: @{user['username']}\n"
        f"👥 Реферер ID: <code>{referrer_tg}</code>\n"
        f"💰 Баланс SD: <b>{user['balance_sd']:.2f} SD</b>\n"
        f"💵 Баланс USDT: <b>{user['balance_usdt']:.2f} USDT</b>\n"
        f"💸 Заработано на заданиях: <b>{earnings:.2f} SD</b>\n"
        f"📱 Телефон: {user['phone'] or '❌ не привязан'}\n"
        f"\n<b>📊 Стейкинг</b>\n"
        f"📦 В стейке: <b>{stake_amount} SD</b>\n"
        f"💰 Заработано: <b>{stake_earned:.2f} SD</b>\n"
        f"🕒 Доход / 24h: <b>{daily_income:.2f} SD</b>\n"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=kb)






from services.ref_reward_service import RefRewardService
from config import REF_PERCENT_LEVEL_1, REF_PERCENT_LEVEL_2

@router.message(F.text == "🤝 Пригласить друга")
async def invite_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={tg_id}"


    cnt = await ReferralsService.count_referrals(tg_id)


    reward = await RefRewardService.get_reward()

    text = (
        "🤝 <b>Пригласить друга</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔗 Твоя реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"👥 Приглашено друзей: <b>{cnt}</b>\n"
        f"💰 Награда за каждого реферала 1 уровня: <b>{reward} SD</b>\n\n"
        "📊 <b>Партнёрские проценты от заданий:</b>\n"
        f"• 1 уровень: <b>{REF_PERCENT_LEVEL_1}%</b>\n"
        f"• 2 уровень: <b>{REF_PERCENT_LEVEL_2}%</b>\n\n"
        "Отправь эту ссылку друзьям — и получай награду за каждого приглашённого,"
        " а также проценты от их заработка на заданиях! 🔥"
    )

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "exchange_menu")
async def open_exchange_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💱 <b>Обмен валют</b>\nВыберите направление:",
        reply_markup=exchange_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "convert_sd_usdt")
async def start_convert_sd(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите количество SD для конвертации в USDT:")
    await state.set_state(ConvertSD.waiting_for_amount)

@router.callback_query(F.data == "convert_usdt_sd")
async def start_convert_usdt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите количество USDT для конвертации в SD:")
    await state.set_state(ConvertUSDT.waiting_for_amount)

@router.message(ConvertSD.waiting_for_amount)
async def convert_sd_amount(message: Message, state: FSMContext):
    from config import SD_PER_USDT
    user = await UserService.get_user(message.from_user.id)

    text = message.text.strip()


    if not text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Введите корректное число")

    amount = float(text)


    if amount > user["balance_sd"]:
        return await message.answer("❌ У вас недостаточно SD")

    #
    usdt = amount / SD_PER_USDT

    await UserService.update_balance_sd(message.from_user.id, user["balance_sd"] - amount)
    await UserService.update_balance_usdt(message.from_user.id, user["balance_usdt"] + usdt)

    await message.answer(f"✅ Успешно!\n{amount} SD → {usdt} USDT")

    await state.clear()

@router.message(ConvertUSDT.waiting_for_amount)
async def convert_usdt_amount(message: Message, state: FSMContext):
    from config import SD_PER_USDT
    user = await UserService.get_user(message.from_user.id)

    text = message.text.strip()


    if not text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Введите корректное число")

    amount = float(text)


    if amount > user["balance_usdt"]:
        return await message.answer("❌ Недостаточно USDT")


    sd = amount * SD_PER_USDT

    await UserService.update_balance_usdt(message.from_user.id, user["balance_usdt"] - amount)
    await UserService.update_balance_sd(message.from_user.id, user["balance_sd"] + sd)

    await message.answer(f"✅ Успешно!\n{amount} USDT → {sd} SD")

    await state.clear()

@router.callback_query(F.data == "profile_history_deposits")
async def profile_history_deposits(callback: types.CallbackQuery,state: FSMContext):

    await state.clear()
    tg_id = callback.from_user.id

    deps = await DepositService.get_by_status("approved")
    deps = [d for d in deps if d["user_id"] == tg_id]

    if not deps:
        return await callback.answer("История пополнений пуста.", show_alert=True)

    text = "<b>📥 История пополнений</b>\n━━━━━━━━━━━━━━\n"

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


@router.callback_query(F.data == "profile_history_withdraws")
async def profile_history_withdraws(callback: types.CallbackQuery,state: FSMContext):

    await state.clear()
    tg_id = callback.from_user.id

    wds = await WithdrawService.get_by_status("approved")
    wds = [w for w in wds if w["user_id"] == tg_id]

    if not wds:
        return await callback.answer("История выводов пуста.", show_alert=True)

    text = "<b>📤 История выводов</b>\n━━━━━━━━━━━━━━\n"

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

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery, state: FSMContext):

    await state.clear()
    tg_id = callback.from_user.id


    user = await UserService.get_user(tg_id)
    stake = await StakingService.get_user(tg_id)

    stake_amount = stake["stake_amount"] or 0
    stake_earned = stake["stake_earned"] or 0

    ref_count = await ReferralsService.count_referrals(tg_id)
    percent = BASE_PERCENT + ref_count * REF_PERCENT
    daily_income = stake_amount * percent / 100
    earnings = await TasksService.get_user_earnings(tg_id)


    has_phone = bool(user["phone"])


    from keyboards.profile import profile_kb
    kb = profile_kb(has_phone)


    text = (
        f"👤 <b>Мой профиль</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 TG ID: <code>{user['tg_id']}</code>\n"
        f"💬 Username: @{user['username']}\n"
        f"👥 Реферер ID: {user['referrer_id']}\n"
        f"💰 Баланс SD: <b>{user['balance_sd']:.2f} SD</b>\n"
        f"💵 Баланс USDT: <b>{user['balance_usdt']:.2f} USDT</b>\n"
        f"💸 Заработано на заданиях: <b>{earnings:.2f} SD</b>\n"
        f"📱 Телефон: {user['phone'] or '❌ не привязан'}\n"
        f"\n<b>📊 Стейкинг</b>\n"
        f"📦 В стейке: <b>{stake_amount} SD</b>\n"
        f"💰 Заработано: <b>{stake_earned:.2f} SD</b>\n"
        f"🕒 Доход / 24h: <b>{daily_income:.2f} SD</b>\n"
    )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


async def show_history(callback, items, prefix: str, page: int):
    total = len(items)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    slice_items = items[start:end]

    if prefix == "hist_dep":
        title = "📥 История пополнений"
    else:
        title = "📤 История выводов"

    text = f"<b>{title}</b> (стр {page+1}/{total_pages})\n━━━━━━━━━━━━━━\n"

    for it in slice_items:
        if prefix == "hist_dep":
            text += (
                f"ID: {it['id']}\n"
                f"Сумма: {it['amount_usdt']} USDT\n"
                f"Метод: {it['method']}\n"
                f"Дата: {pretty_date(it['created_at'])}\n"
                "----------------------\n"
            )
        else:
            text += (
                f"ID: {it['id']}\n"
                f"Сумма: {it['amount_usdt']} USDT\n"
                f"Метод: {it['method']}\n"
                f"Кошелёк: {it['wallet']}\n"
                f"Дата: {pretty_date(it['created_at'])}\n"
                "----------------------\n"
            )

    kb = history_nav_kb(prefix, page, total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("hist_dep:"))
async def user_history_deposits(callback: types.CallbackQuery,state: FSMContext):

    await state.clear()
    page = int(callback.data.split(":")[1])
    tg_id = callback.from_user.id

    deps = await DepositService.get_by_status("approved")
    deps = [d for d in deps if d["user_id"] == tg_id]

    if not deps:
        return await callback.answer("История пополнений пуста.", show_alert=True)

    await show_history(callback, deps, "hist_dep", page)

@router.callback_query(F.data.startswith("hist_wd:"))
async def user_history_withdraws(callback: types.CallbackQuery,state: FSMContext):

    await state.clear()
    page = int(callback.data.split(":")[1])
    tg_id = callback.from_user.id

    wds = await WithdrawService.get_by_status("approved")
    wds = [w for w in wds if w["user_id"] == tg_id]

    if not wds:
        return await callback.answer("История выводов пуста.", show_alert=True)

    await show_history(callback, wds, "hist_wd", page)

@router.message(F.text == "🎁 Бонусы")
async def open_bonus_menu(message: types.Message):

    await message.answer("🎁 <b>Бонусы</b>\n"
    "Добро пожаловать в раздел бонусов!\n\n"
    "🎁 <b>Ежедневный бонус:</b> получайте SD раз в 24 часа, если все задания выполнены.\n"
    "⚒ <b>Майнеры:</b> покупайте майнеры и собирайте автоматический доход SD.\n"
    "💎 <b>Стейкинг:</b> замораживайте SD и получайте прибыль ежедневно.\n"
    "🎟 <b>Лотерея:</b> участвуйте и выигрывайте дополнительные награды.\n", reply_markup=bonus_menu_kb())

@router.callback_query(F.data == "daily_bonus")
async def daily_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tasks_left = await TasksService.get_available_tasks_for_user(user_id, limit=1)
    if tasks_left:
        return await callback.answer(
            "❌ Нельзя получить ежедневный бонус, пока у вас есть доступные задания.\n"
            "Сначала выполните все задания в разделе «🎯 Задания».",
            show_alert=True
        )

    if not await BonusService.can_claim_bonus(user_id):
        return await callback.answer("⚠ Бонус уже получен. Возвращайтесь через 24 часа!", show_alert=True)

    amount = round(random.uniform(0.5, 1.0), 2)

    await BonusService.give_bonus(user_id, amount)

    await callback.message.edit_text(
        f"🎉 <b>Ежедневный бонус получен!</b>\n"
        f"+<b>{amount} SD</b> на ваш баланс.\n\n"
        f"Возвращайтесь завтра!",
        reply_markup=None
    )

    await callback.answer()


@router.message(lambda m: m.text == "🛠️ Тех. поддержка")
async def support_reply_handler(message: types.Message):

    user = message.from_user


    if not user.username:
        await message.answer(
            "⚠️ У вас не установлен @username.\n\n"
            "Чтобы техподдержка могла вам ответить:\n"
            "Откройте Telegram → Настройки → Имя пользователя."
        )
        return

    url = f"https://t.me/{SUPPORT_USERNAME}"

    try:
        await message.answer(
            "🛠 Открываю чат с поддержкой…\n"
            f"Если не открыло автоматически — нажмите:\n\n"
            f"👉 @{SUPPORT_USERNAME}\n\n"
            f"Или перейдите по ссылке:\n{url}"
        )

    except Exception as e:
        await message.answer(
            "⚠️ Не удалось открыть чат поддержки.\n"
            "Попробуйте перейти вручную:\n"
            f"👉 @{SUPPORT_USERNAME}"
        )

@router.callback_query(F.data == "confirm_phone")
async def request_phone(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PhoneState.entering_phone)

    await callback.message.answer(
        "📱 <b>Подтвердите номер телефона</b>\n\n"
        "Нажмите кнопку ниже — Telegram отправит ваш реальный номер.",
        reply_markup=phone_request_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(PhoneState.entering_phone, F.contact)
async def save_phone(message: types.Message, state: FSMContext):

    phone = message.contact.phone_number


    phone = phone.replace(" ", "").replace("-", "")


    if not phone.startswith("+"):
        phone = "+" + phone


    if not any(phone.startswith(p) for p in ALLOWED_PREFIXES):
        await message.answer(
            "❌ <b>Номер не подходит</b>\n\n"
            "Разрешены только номера стран СНГ и Польши.\n"
            "Попробуйте другой номер.",
            parse_mode="HTML",
            reply_markup=main_menu
        )
        return

    # сохраняем в БД
    db = await get_db()
    await db.execute(
        "UPDATE users SET phone = ? WHERE tg_id = ?",
        (phone, message.from_user.id)
    )
    await db.commit()
    await db.close()

    await message.answer(
        f"✅ Номер <b>{phone}</b> успешно подтверждён!",
        parse_mode="HTML",
        reply_markup=main_menu
    )

    await state.clear()


    await message.answer("Возвращаю в профиль…")
    await profile_cmd(message, state)

@router.callback_query(F.data == "enter_promo")
async def ask_promo(callback: types.CallbackQuery, state: FSMContext):
    tasks_left = await TasksService.get_available_tasks_for_user(callback.from_user.id, limit=1)

    if tasks_left:
        return await callback.answer(
            "❌ Вы не можете активировать промокод, пока у вас есть доступные задания.\n"
            "Сначала выполните все задания в разделе «🎯 Задания».",
            show_alert=True
        )
    await callback.answer()
    await callback.message.answer("Введите промокод:")
    await state.set_state(PromoState.waiting_code)


@router.message(PromoState.waiting_code)
async def activate_promo(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.clear()

    result = await PromoCodeService.activate(message.from_user.id, code)

    if result["status"] == "ok":
        return await message.answer(f"🎉 Промокод активирован! +{result['reward']} SD")

    if result["status"] == "not_found":
        return await message.answer("❌ Неверный промокод")

    if result["status"] == "limit_reached":
        return await message.answer("⚠ Лимит промокода исчерпан")

    if result["status"] == "already_used":
        return await message.answer("⚠ Вы уже использовали этот промокод")

    await message.answer("Ошибка промокода.")
@router.callback_query(F.data == "profile_settings")
async def open_profile_settings(callback: types.CallbackQuery):
    tg_id = callback.from_user.id

    db = await get_db()
    cur = await db.execute("SELECT phone FROM users WHERE tg_id = ?", (tg_id,))
    user = await cur.fetchone()
    await db.close()

    has_phone = bool(user["phone"]) if user else False

    await callback.message.edit_text(
        "⚙ <b>Настройки профиля</b>",
        reply_markup=profile_settings_kb(has_phone),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "lottery_buy")
async def lottery_buy(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    db = await get_db()


    cur = await db.execute("SELECT 1 FROM lottery_tickets WHERE user_id = ?", (user_id,))
    exists = await cur.fetchone()

    if exists:
        await callback.answer("❗ У вас уже есть билет в текущей лотерее.", show_alert=True)
        await db.close()
        return


    cur = await db.execute("SELECT balance_sd FROM users WHERE tg_id = ?", (user_id,))
    user = await cur.fetchone()

    if not user:
        await callback.answer("⚠ Пользователь не найден в системе.", show_alert=True)
        await db.close()
        return

    balance = user["balance_sd"] or 0

    if balance < 10:
        await callback.answer("❌ Недостаточно SD. Цена билета — 10 SD.", show_alert=True)
        await db.close()
        return


    await db.execute(
        "UPDATE users SET balance_sd = balance_sd - 10 WHERE tg_id = ?",
        (user_id,)
    )


    now = int(time.time())
    await db.execute(
        "INSERT INTO lottery_tickets (user_id, created_at) VALUES (?, ?)",
        (user_id, now)
    )

    await db.commit()
    await db.close()

    await callback.message.edit_text(
        "🎟 Вы успешно купили билет в лотерее!\n"
        "Ожидайте розыгрыша — админ запустит его вручную.",
        reply_markup=None
    )
    await callback.answer()

@router.callback_query(F.data == "miners_menu")
async def miners_menu(callback: types.CallbackQuery):
    tg_id = callback.from_user.id


    refs = await ReferralsService.count_referrals(tg_id)


    miners = await MinerService.get_user_miners(tg_id)

    has_m1 = any(m["miner_type"] == 1 for m in miners)
    has_m2 = any(m["miner_type"] == 2 for m in miners)

    text = (
        "⚒ <b>Майнеры SD</b>\n\n"
        f"👥 Приглашено друзей: <b>{refs}</b>\n\n"
        "Доступные майнеры:\n"
        "1) Майнер 1 — цена <b>100 SD</b>, доход <b>1 SD / 24ч</b>, требуется <b>5</b> друзей.\n"
        "2) Майнер 2 — цена <b>500 SD</b>, доход <b>5 SD / 24ч</b>, требуется <b>10</b> друзей.\n\n"
        "Ваши майнеры:\n"
    )

    if not miners:
        text += "• У вас пока нет майнеров.\n"
    else:
        for m in miners:
            if m["miner_type"] == 1:
                text += "• Майнер 1 (1 SD / 24ч)\n"
            elif m["miner_type"] == 2:
                text += "• Майнер 2 (5 SD / 24ч)\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏ Купить Майнер 1", callback_data="miner_buy_1")],
        [InlineKeyboardButton(text="⛏ Купить Майнер 2", callback_data="miner_buy_2")],
        [InlineKeyboardButton(text="💰 Забрать прибыль", callback_data="miner_claim")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_bonus")],
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "back_to_bonus")
async def back_to_bonus(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 <b>Бонусы</b>\n"
    "Добро пожаловать в раздел бонусов!\n\n"
    "🎁 <b>Ежедневный бонус:</b> получайте SD раз в 24 часа, если все задания выполнены.\n"
    "⚒ <b>Майнеры:</b> покупайте майнеры и собирайте автоматический доход SD.\n"
    "💎 <b>Стейкинг:</b> замораживайте SD и получайте прибыль ежедневно.\n"
    "🎟 <b>Лотерея:</b> участвуйте и выигрывайте дополнительные награды.\n",
        reply_markup=bonus_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
@router.callback_query(F.data == "miner_buy_1")
async def miner_buy_1(callback: types.CallbackQuery):
    await _buy_miner(callback, 1)

@router.callback_query(F.data == "miner_buy_2")
async def miner_buy_2(callback: types.CallbackQuery):
    await _buy_miner(callback, 2)


async def _buy_miner(callback: types.CallbackQuery, miner_type: int):
    tg_id = callback.from_user.id
    result = await MinerService.buy_miner(tg_id, miner_type)

    cfg = {1: {"price": 100, "min_refs": 5}, 2: {"price": 500, "min_refs": 10}}[miner_type]
    name = "Майнер 1" if miner_type == 1 else "Майнер 2"

    status = result["status"]

    if status == "invalid_type":
        return await callback.answer("Ошибка типа майнера.", show_alert=True)

    if status == "no_user":
        return await callback.answer("Пользователь не найден.", show_alert=True)

    if status == "not_enough_refs":
        need = result["need"]
        have = result["have"]
        return await callback.answer(
            f"❌ Недостаточно приглашённых друзей.\n"
            f"Нужно:{need}, у вас: <b>{have}.",
            show_alert=True
        )

    if status == "not_enough_balance":
        price = result["price"]
        balance = result["balance"]
        return await callback.answer(
            f"❌ Недостаточно SD для покупки.\n"
            f"Цена: {price} SD, у вас: {balance:.2f} SD.",
            show_alert=True
        )

    if status == "already_bought":
        return await callback.answer(
            "❗ Этот майнер уже куплен.\n"
            "Вы можете собирать с него прибыль в разделе «Майнеры».",
            show_alert=True
        )

    if status == "ok":
        price = result["price"]
        await callback.answer(
            f"✅ {name} успешно куплен за <b>{price} SD</b>!",
            show_alert=True
        )

        return await miners_menu(callback)


    return await callback.answer("Ошибка при покупке майнера.", show_alert=True)
@router.callback_query(F.data == "miner_claim")
async def miner_claim(callback: types.CallbackQuery):
    tg_id = callback.from_user.id

    result = await MinerService.claim_income(tg_id)
    status = result["status"]

    if status == "no_user":
        return await callback.answer("Пользователь не найден.", show_alert=True)

    if status == "no_miners":
        return await callback.answer(
            "❌ У вас ещё нет майнеров.\nКупите майнер в разделе «Майнеры».",
            show_alert=True
        )

    if status == "nothing_to_claim":
        return await callback.answer(
            "⏳ Пока нечего забирать.\nЗайдите чуть позже, чтобы собрать доход.",
            show_alert=True
        )

    if status == "ok":
        amount = result["amount"]
        amount = round(amount, 4)
        await callback.answer(
            f"💰 Доход собран: <b>{amount} SD</b>!",
            show_alert=True
        )

        return await miners_menu(callback)

    return await callback.answer("Ошибка при сборе дохода.", show_alert=True)
