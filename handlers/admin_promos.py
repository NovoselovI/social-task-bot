from aiogram import Router,types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.promocode_service import PromoCodeService
from states.promo_states import PromoCreateState

router = Router()


@router.callback_query(F.data == "admin_promocodes")
async def admin_promos(callback: types.CallbackQuery):
    await show_promocodes(callback, 0)


async def show_promocodes(callback: types.CallbackQuery, offset: int):
    promos, total = await PromoCodeService.get_paginated(offset)
    kb = []

    if promos:
        for p in promos:
            kb.append([InlineKeyboardButton(
                text=f"{p['code']} (+{p['reward_sd']} SD) {p['used_count']}/{p['max_uses']}",
                callback_data=f"del_promo_{p['id']}"
            )])

    if offset + 5 < total:
        kb.append([InlineKeyboardButton(
            text="➡ Показать ещё",
            callback_data=f"admin_promos_next_{offset+5}"
        )])

    kb.append([InlineKeyboardButton(text="➕ Создать", callback_data="create_promo")])


    await callback.message.edit_text(
        "<b>🧾 Промокоды</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_promos_next_"))
async def next_page(callback: types.CallbackQuery):
    offset = int(callback.data.split("_")[-1])
    await show_promocodes(callback, offset)


@router.callback_query(F.data.startswith("del_promo_"))
async def delete_promo(callback: types.CallbackQuery):
    promo_id = int(callback.data.split("_")[-1])
    await PromoCodeService.delete(promo_id)

    await callback.answer("Промокод удалён")
    await admin_promos(callback)


@router.callback_query(F.data == "create_promo")
async def create_promo(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PromoCreateState.waiting_for_code)
    await callback.message.edit_text("Введите промокод:")
    await callback.answer()


@router.message(PromoCreateState.waiting_for_code)
async def promo_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(code=code)

    await state.set_state(PromoCreateState.waiting_for_reward)
    await message.answer("Введите награду в SD:")


@router.message(PromoCreateState.waiting_for_reward)
async def promo_reward(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число.")

    reward = int(message.text)
    await state.update_data(reward=reward)

    await state.set_state(PromoCreateState.waiting_for_limit)
    await message.answer("Введите лимит использований:")


@router.message(PromoCreateState.waiting_for_limit)
async def promo_limit(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число.")

    limit = int(message.text)
    data = await state.get_data()

    result = await PromoCodeService.create(
        data["code"], data["reward"], limit
    )

    if result["status"] == "exists":
        return await message.answer("❌ Такой промокод уже существует!")

    await state.clear()
    await message.answer("🎉 Промокод создан!")
