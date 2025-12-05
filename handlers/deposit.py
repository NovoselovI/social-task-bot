from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.deposit import deposit_methods_kb, confirm_payment_kb
from keyboards.main_menu import main_menu
from services.deposit_service import DepositService

from config import UAH_TO_USDT_RATE


router = Router()


class DepositState(StatesGroup):
    entering_amount = State()




@router.callback_query(F.data == "profile_deposit")
async def deposit_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "💰 Выберите способ пополнения:",
        reply_markup=deposit_methods_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_method:"))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):

    method = callback.data.split(":", 1)[1]

    await state.update_data(method=method)

    if method == "ton":
        await callback.message.edit_text("Введите сумму пополнения в USDT:")

    elif method == "bep20":
        await callback.message.edit_text("Введите сумму пополнения в USDT:")

    elif method == "uah":
        await callback.message.edit_text(
            f"Введите сумму в UAH.\n"
            f"💱 Курс: 1 USDT = {UAH_TO_USDT_RATE}₴"
        )
    await state.set_state(DepositState.entering_amount)
    await callback.answer()

@router.message(DepositState.entering_amount)
async def deposit_enter_amount(message: types.Message, state: FSMContext):
    raw = message.text.replace(",", ".")
    try:
        amount = float(raw)
        if amount <= 0:
            raise ValueError()
    except Exception:
        return await message.answer("❌ Введите корректное положительное число, например 10 или 10.5")

    data = await state.get_data()
    method = data.get("method")

    if not method:
        await state.clear()
        return await message.answer("Произошла ошибка: не выбран метод пополнения. Попробуйте ещё раз.")

    # ---------- Минимальный депозит ----------
    if method in ("ton", "bep20"):
        if amount < 1:
            return await message.answer("❌ Минимальный депозит — 1 USDT.")

    elif method == "uah":
        min_uah = UAH_TO_USDT_RATE * 1
        if amount < min_uah:
            return await message.answer(
                f"❌ Минимальный депозит — {min_uah:.0f} ₴ (эквивалент 1 USDT)."
            )

    await state.update_data(amount=amount)

    # ======================================================
    #                         TON
    # ======================================================
    if method == "ton":
        ton_address = await DepositService.get_setting("TON_ADDRESS") or "Не задан"
        memo = str(message.from_user.id)

        requisites = (
            "💎 <b>Пополнение USDT (TON)</b>\n\n"
            "<b>1)</b> Отправьте сумму на адрес:\n"
            f"<code>{ton_address}</code>\n\n"
            "<b>2)</b> Укажите MEMO:\n"
            f"<code>{memo}</code>\n\n"
            "После отправки нажмите «Я оплатил»."
        )
        amount_text = f"{amount} USDT"

    # ======================================================
    #                        BEP20
    # ======================================================
    elif method == "bep20":
        bep20_address = await DepositService.get_setting("BEP20_ADDRESS") or "Не задан"

        requisites = (
            "🔶 <b>BEP20 USDT адрес:</b>\n"
            f"<code>{bep20_address}</code>"
        )
        amount_text = f"{amount} USDT"

    # ======================================================
    #                          UAH
    # ======================================================
    elif method == "uah":
        uah_req = await DepositService.get_setting("UAH_REQUISITES") or "Реквизиты не заданы"

        requisites = (
            "🇺🇦 <b>Реквизиты для оплаты (UAH):</b>\n"
            f"<code>{uah_req}</code>"
        )
        amount_text = f"{amount} UAH"

    else:
        return await message.answer("❌ Неизвестный метод пополнения.")

    # отправляем универсальное сообщение
    await message.answer(
        f"💵 Сумма: <b>{amount_text}</b>\n"
        f"Метод: <b>{method.upper()}</b>\n\n"
        f"{requisites}\n\n"
        "После оплаты нажмите кнопку ниже:",
        parse_mode="HTML",
        reply_markup=confirm_payment_kb(method, amount)
    )

    await state.clear()






@router.callback_query(F.data.startswith("dep_paid:"))
async def deposit_paid(callback: types.CallbackQuery):
    try:
        _, method, amount_str = callback.data.split(":")
        amount = float(amount_str)
    except Exception:
        await callback.answer("Ошибка в данных платежа.", show_alert=True)
        return

    user_id = callback.from_user.id
    recent = await DepositService.count_recent(user_id, minutes=10)
    if recent >= 5:
        return await callback.answer(
            "❌ Слишком много заявок на пополнение.\n"
            "Разрешено не более 5 заявок за 10 минут.",
            show_alert=True
        )

    dep_id = await DepositService.create_deposit(user_id, amount, method)


    await DepositService.notify_admins_about_deposit(
        callback.bot,
        dep_id,
        user_id,
        amount,
        method
    )


    await callback.message.edit_text(
        "⏳ Платёж отправлен на проверку администратору.\n"
        "Обычно это занимает несколько минут 😊"
    )


    await callback.message.answer(
        "Возвращаю в главное меню.",
        reply_markup=main_menu
    )

    await callback.answer("Отправлено на проверку!")
