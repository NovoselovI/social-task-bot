from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.staking_kb import staking_main_kb
from services.staking_service import StakingService
from services.referrals_service import ReferralsService
import datetime

router = Router()

MIN_STAKE = 10
MAX_STAKE = 10000
BASE_PERCENT = 0.25  # %
REF_PERCENT = 0.01   # %

class StakeState(StatesGroup):
    entering_amount = State()


@router.callback_query(F.data == "bonus_staking")
async def open_staking(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    data = await StakingService.get_user(user_id)
    refs = await StakingService.get_referrals_count(user_id)

    percent = BASE_PERCENT + refs * REF_PERCENT


    stake_amount = data["stake_amount"] or 0
    stake_earned = data["stake_earned"] or 0
    ref_count = await ReferralsService.count_referrals(user_id)
    ref_bonus = ref_count * REF_PERCENT


    daily_income = stake_amount * percent / 100
    text = (
        "💹 <b>Стейкинг SD!\n Забирай награду каждые 24 часа!</b>\n\n"
        "📈 <b>Процент за 24 часа:</b>\n"
        f"— Базовый: <b>{BASE_PERCENT:.2f}%</b>\n"
        f"— За рефералов: <b>{ref_count} × 0.01% = {ref_bonus:.2f}%</b>\n"
        "----------------------------------------\n"
        f"👉 Итоговый процент: <b>{percent:.2f}%</b>\n\n"
        f"📦 <b>В стейкинге:</b> {stake_amount} SD\n"
        f"💰 <b>Всего заработано:</b> {stake_earned:.2f} SD\n"
        f"🕒 <b>Доход за 24 часа:</b> {daily_income:.2f} SD\n\n"
        f"🔒 Минимум для стейка: {MIN_STAKE} SD\n"
        f"🎯 Максимум: {MAX_STAKE} SD"
    )

    await callback.message.edit_text(text, reply_markup=staking_main_kb())
    await callback.answer()



@router.callback_query(F.data == "stake_add")
async def stake_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите сумму SD для стейкинга:")
    await state.set_state(StakeState.entering_amount)
    await callback.answer()


@router.message(StakeState.entering_amount)
async def stake_amount_enter(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount < MIN_STAKE:
            return await message.answer(f"Минимальный стейк — {MIN_STAKE} SD.")
    except:
        return await message.answer("Введите число.")

    user_id = message.from_user.id
    user_data = await StakingService.get_user(user_id)

    from database.db import get_db

    db = await get_db()
    cur = await db.execute("SELECT balance_sd FROM users WHERE tg_id = ?", (user_id,))
    balance_row = await cur.fetchone()
    await db.close()

    if balance_row["balance_sd"] < amount:
        return await message.answer("❌ Недостаточно SD на балансе.")

    current_stake = user_data["stake_amount"]
    if current_stake + amount > MAX_STAKE:
        return await message.answer(f"Максимальный стейк — {MAX_STAKE} SD.")


    await StakingService.update_stake(user_id, amount)

    await state.clear()
    await message.answer(f"✔ Вы успешно застейкали {amount} SD!", reply_markup=None)


#
@router.callback_query(F.data == "stake_withdraw")
async def stake_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await StakingService.get_user(user_id)

    if user["stake_amount"] <= 0:
        return await callback.answer("У вас нет застейканных SD.", show_alert=True)

    amount = await StakingService.withdraw_stake(user_id)

    await callback.message.edit_text(f"📤 Вам возвращено {amount} SD.")
    await callback.answer()



@router.callback_query(F.data == "stake_claim")
async def stake_claim(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await StakingService.get_user(user_id)
    refs = await StakingService.get_referrals_count(user_id)

    stake_amount = user["stake_amount"]
    if stake_amount <= 0:
        return await callback.answer("У вас нет стейка.", show_alert=True)

    last = user["stake_last_claim"]
    now = datetime.datetime.utcnow()

    if last:
        last_dt = datetime.datetime.fromisoformat(last)
        diff = (now - last_dt).total_seconds()
        if diff < 86400:
            return await callback.answer("⏳ Ещё не прошло 24 часа.", show_alert=True)

    percent = BASE_PERCENT + refs * REF_PERCENT
    reward = stake_amount * percent / 100

    await StakingService.update_claim(user_id, reward)

    await callback.answer(f"💰 Вы получили {reward:.2f} SD!", show_alert=True)
