from aiogram import Router, types, F
from aiogram.filters import Command

from aiogram.fsm.context import FSMContext

from handlers.restrictred import pretty_date
from services.deposit_service import DepositService
from services.withdraw_service import  WithdrawService
from keyboards.admin_finance import (
    finance_menu_kb,
    deposit_statuses_kb,
    deposits_list_kb,
    deposit_details_kb,
    withdraw_details_kb,
    withdraw_statuses_kb,
    withdraws_list_kb,

)

router = Router()

ITEMS_PER_PAGE = 20


@router.message(Command("finance"))
async def admin_finance(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💼 <b>Управление финансами</b>\nВыберите раздел:",
        reply_markup=finance_menu_kb()
    )


@router.callback_query(F.data == "finance_deposits")
async def open_deposits_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Пополнения</b>\nВыберите статус:",
        reply_markup=deposit_statuses_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "finance_back_to_main")
async def back_to_main_finance(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💼 <b>Управление финансами</b>\nВыберите раздел:",
        reply_markup=finance_menu_kb()
    )
    await callback.answer()


async def _show_deposits(callback: types.CallbackQuery, status: str, page: int):
    all_deps = await DepositService.get_by_status(status)

    if not all_deps:
        return await callback.answer("Нет заявок.", show_alert=True)

    total = len(all_deps)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    page = max(0, min(page, total_pages - 1))  # защита

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    deps = all_deps[start:end]

    text = f"📄 <b>{status.upper()}</b> (стр. {page + 1}/{total_pages})\n━━━━━━━━━━━━━━"

    kb = deposits_list_kb(deps, status, page, total_pages)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("dep_list:"))
async def list_deposits(callback: types.CallbackQuery):
    _, status, page = callback.data.split(":")
    await _show_deposits(callback, status, int(page))


@router.callback_query(F.data.startswith("dep_view:"))
async def open_deposit(callback: types.CallbackQuery):
    _, dep_id, status, page = callback.data.split(":")
    dep = await DepositService.get_deposit(int(dep_id))

    if not dep:
        return await callback.answer("Заявка не найдена", show_alert=True)

    text = (
        f"💰 <b>Заявка #{dep['id']}</b>\n"
        f"👤 Пользователь: <code>{dep['user_id']}</code>\n"
        f"💵 Сумма: {dep['amount_usdt']} USDT\n"
        f"Метод: {dep['method']}\n"
        f"Дата: {pretty_date(dep['created_at'])} (UTC)\n"

        f"Статус: {dep['status']}"
    )

    kb = deposit_details_kb(int(dep_id), status, int(page))
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("dep_approve:"))
async def approve_deposit(callback: types.CallbackQuery):
    _, dep_id, status, page = callback.data.split(":")
    dep_id = int(dep_id)
    page = int(page)

    result = await DepositService.approve_deposit(dep_id)

    if result == "already_processed":
        return await callback.answer("⚠ Эта заявка уже обработана другим администратором.", show_alert=True)

    if result == "not_found":
        return await callback.answer("❌ Заявка не найдена.", show_alert=True)

    if status == "notify":
        await callback.message.edit_text("✅ Пополнение зачислено.")
        return await callback.answer()

    return await _show_deposits(callback, status, page)


@router.callback_query(F.data.startswith("dep_decline:"))
async def decline_deposit(callback: types.CallbackQuery):
    _, dep_id, status, page = callback.data.split(":")
    dep_id = int(dep_id)
    page = int(page)

    result = await DepositService.decline_deposit(dep_id)

    if result == "already_processed":
        return await callback.answer("⚠ Эта заявка уже обработана.", show_alert=True)

    if result == "not_found":
        return await callback.answer("❌ Заявка не найдена.", show_alert=True)

    if status == "notify":
        await callback.message.edit_text("❌ Пополнение отклонено.")
        return await callback.answer()

    return await _show_deposits(callback, status, page)



@router.callback_query(F.data == "finance_withdraws")
async def open_withdraws_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💸 <b>Выводы</b>\nВыберите статус:",
        reply_markup=withdraw_statuses_kb()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("approve_wd:"))
async def approve_wd(callback: types.CallbackQuery):
    wd_id = int(callback.data.split(":")[1])

    result = await WithdrawService.approve_withdraw(wd_id)

    if result == "insufficient":
        return await callback.answer("❌ Недостаточно средств на балансе пользователя.", show_alert=True)

    if result == "already_processed":
        return await callback.answer("⚠ Эта заявка уже обработана другим администратором.", show_alert=True)

    if result == "not_found":
        return await callback.answer("❌ Заявка не найдена.", show_alert=True)

    wd = await WithdrawService.get_withdraw(wd_id)

    await callback.message.edit_text("✔️ Вывод подтверждён.")
    await callback.bot.send_message(
        wd["user_id"],
        f"🎉 Ваш вывод {wd['amount_usdt']} USDT подтверждён!"
    )
    await callback.answer()



@router.callback_query(F.data.startswith("decline_wd:"))
async def decline_wd(callback: types.CallbackQuery, state: FSMContext):
    wd_id = int(callback.data.split(":")[1])

    result = await WithdrawService.decline_withdraw(wd_id)

    if result == "already_processed":
        return await callback.answer("⚠ Заявка уже обработана другим администратором.", show_alert=True)

    if result == "not_found":
        return await callback.answer("❌ Заявка не найдена.", show_alert=True)

    wd = await WithdrawService.get_withdraw(wd_id)

    text = (
        f"📤 <b>Вывод #{wd['id']}</b>\n"
        f"Сумма: {wd['amount_usdt']} USDT\n"
        f"Метод: {wd['method']}\n"
        f"Кошелёк: <code>{wd['wallet']}</code>\n"
        f"Дата: {pretty_date(wd['created_at'])}\n\n"
        f"Статус: ❌ <b>Отклонён</b> ({pretty_date(wd['processed_at'])})"
    )

    await callback.message.edit_text(text)
    await callback.bot.send_message(
        wd["user_id"],
        f"❌ Ваш вывод {wd['amount_usdt']} USDT был отклонён."
    )
    await callback.answer()




async def _show_withdraws(callback: types.CallbackQuery, status: str, page: int):
    all_wd = await WithdrawService.get_by_status(status)

    if not all_wd:
        return await callback.answer("Нет заявок.", show_alert=True)

    total = len(all_wd)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    items = all_wd[start:end]

    text = f"📄 <b>{status.upper()}</b> (стр. {page + 1}/{total_pages})\n━━━━━━━━━━━━━━"

    kb = withdraws_list_kb(items, status, page, total_pages)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("wd_list:"))
async def list_withdraws(callback: types.CallbackQuery):
    _, status, page = callback.data.split(":")
    await _show_withdraws(callback, status, int(page))


@router.callback_query(F.data.startswith("wd_view:"))
async def open_withdraw(callback: types.CallbackQuery):
    _, wd_id, status, page = callback.data.split(":")
    wd = await WithdrawService.get_withdraw(int(wd_id))

    if not wd:
        return await callback.answer("Заявка не найдена", show_alert=True)

    text = (
        f"📤 <b>Вывод #{wd['id']}</b>\n"
        f"👤 Пользователь: <code>{wd['user_id']}</code>\n"
        f"💵 Сумма: {wd['amount_usdt']} USDT\n"
        f"Метод: {wd['method']}\n"
        f"Кошелёк: <code>{wd['wallet']}</code>\n"
        f"Дата: {pretty_date(wd['created_at'])}\n"
        f"Статус: {wd['status']}"
    )

    kb = withdraw_details_kb(int(wd_id), status, int(page))
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("wd_approve:"))
async def approve_wd(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    wd_id = int(parts[1])


    result = await WithdrawService.approve_withdraw(wd_id)


    if result == "insufficient":
        await callback.answer("❌ Недостаточно средств на балансе пользователя.", show_alert=True)
        return
    if result == "already_processed":
        return await callback.answer("⚠ Эта заявка уже обработана другим администратором.", show_alert=True)

    if result == "not_found":
        return await callback.answer("❌ Заявка не найдена.", show_alert=True)

    await callback.message.edit_text("✔️ Вывод подтверждён.")
    await callback.answer()


@router.callback_query(F.data.startswith("wd_decline:"))
async def decline_withdraw(callback: types.CallbackQuery):
    _, wd_id, status, page = callback.data.split(":")
    wd_id = int(wd_id)
    page = int(page)

    await WithdrawService.decline_withdraw(wd_id)

    if status == "notify":
        await callback.message.edit_text("❌ Вывод отклонён.")
        return await callback.answer()

    return await _show_withdraws(callback, status, page)