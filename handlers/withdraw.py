from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.withdraw_states import WithdrawState
from keyboards.withdraw_kb import withdraw_methods_kb
from services.withdraw_service import WithdrawService
from services.user_service import UserService
from services.deposit_service import DepositService

router = Router()

@router.callback_query(F.data == "profile_withdraw")
async def withdraw_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    await state.set_state(WithdrawState.choosing_method)
    await callback.message.answer(
        "Выберите метод вывода:",
        reply_markup=withdraw_methods_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wd_method:"))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split(":")[1]

    await state.update_data(method=method)
    await state.set_state(WithdrawState.entering_amount)

    await callback.message.edit_text(
        "Введите сумму в USDT, которую хотите вывести:"
    )

    await callback.answer()


@router.message(WithdrawState.entering_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    user = await UserService.get_user(tg_id)
    if not user["phone"]:
        return await message.answer("⚠️ Подтвердите номер телефона, чтобы выводить средства.")

    raw = message.text.replace(",", ".")
    try:
        amount = float(raw)
    except:
        return await message.answer("❌ Введите корректное число.")

    min_withdraw = await DepositService.get_setting("MIN_WITHDRAW") or 20

    if amount < float(min_withdraw):
        return await message.answer(f"❌ Минимальный вывод: {min_withdraw} USDT")

    if amount > user["balance_usdt"]:
        return await message.answer("❌ Недостаточно средств.")

    await state.update_data(amount=amount)
    await message.answer("Введите адрес кошелька:")
    await state.set_state(WithdrawState.entering_wallet)



@router.message(WithdrawState.entering_wallet)
async def withdraw_wallet(message: types.Message, state: FSMContext):
    wallet = message.text.strip()


    data = await state.get_data()

    amount = data["amount"]
    method = data["method"]

    if await WithdrawService.has_pending(message.from_user.id):
        await state.clear()
        return await message.answer(
            "❌ У вас уже есть активная заявка на вывод. Дождитесь её обработки."
        )

    dep_id = await WithdrawService.create_withdraw(
        user_id=message.from_user.id,
        amount_usdt=amount,
        method=method,
        wallet=wallet
    )

    await WithdrawService.notify_admins_about_withdraw(
        bot=message.bot,
        wd_id=dep_id,
        user_id=message.from_user.id,
        amount=amount,
        method=method,
        wallet=wallet
    )

    await message.answer(
        f"📤 Заявка на вывод создана!\n"
        f"Сумма: <b>{amount} USDT</b>\n"
        f"Метод: <b>{method.upper()}</b>\n"
        f"Кошелёк: <code>{wallet}</code>\n\n"
        "После проверки админом будет произведён вывод."
    )

    await state.clear()
