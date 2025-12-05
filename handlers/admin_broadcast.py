from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from database.db import get_db
from config import ADMINS
from states.broadcast_states import BroadcastStates
import asyncio

router = Router()
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
        "<b>Меню рассылки</b>\nВыберите тип:",
        reply_markup=broadcast_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "bc_text")
async def bc_text_start(callback: types.CallbackQuery, state):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(BroadcastStates.text)
    await callback.message.answer("✏️ Введите текст рассылки:")
    await callback.answer()

@router.message(BroadcastStates.text)
async def bc_text_process(message: types.Message, state):
    await state.clear()
    text = message.text

    status_msg = await message.answer("⏳ Подготовка рассылки...")

    asyncio.create_task(run_broadcast_text(message.bot, text, status_msg))

    await message.answer("🚀 Рассылка запущена в фоне.")

async def run_broadcast_text(bot, text, status_msg):
    db = await get_db()
    users = await db.execute_fetchall("SELECT tg_id FROM users WHERE is_banned = 0")
    await db.close()

    total = len(users)
    sent = 0

    for row in users:
        user_id = row["tg_id"]

        try:
            await bot.send_message(user_id, text)
            sent += 1

        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramForbiddenError:
            pass
        except Exception:
            pass


        if sent % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"📣 Рассылка выполняется…\n"
                    f"Отправлено: <b>{sent}</b> из <b>{total}</b>"
                )
            except:
                pass

        await asyncio.sleep(0.08)


    try:
        await status_msg.edit_text(
            f"✅ Рассылка завершена!\n"
            f"Отправлено: <b>{sent}</b> из <b>{total}</b>"
        )
    except:
        pass

@router.callback_query(F.data == "bc_photo")
async def bc_photo_start(callback: types.CallbackQuery, state):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(BroadcastStates.photo)
    await callback.message.answer("📷 Отправьте фото и подпись:")
    await callback.answer()

@router.message(F.photo, BroadcastStates.photo)

async def bc_photo_process(message: types.Message, state):
    await state.clear()

    photo = message.photo[-1].file_id
    caption = message.caption or ""

    status_msg = await message.answer("⏳ Подготовка рассылки...")

    asyncio.create_task(
        run_broadcast_photo(message.bot, photo, caption, status_msg)
    )

    await message.answer("🚀 Рассылка запущена в фоне.")

async def run_broadcast_photo(bot, photo_id, caption, status_msg):
    db = await get_db()
    users = await db.execute_fetchall("SELECT tg_id FROM users WHERE is_banned = 0")
    await db.close()

    total = len(users)
    sent = 0

    for row in users:
        user_id = row["tg_id"]

        try:
            await bot.send_photo(user_id, photo_id, caption=caption)
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramForbiddenError:
            pass
        except Exception:
            pass

        if sent % 15 == 0:
            try:
                await status_msg.edit_text(
                    f"🖼 Рассылка фото…\n"
                    f"Отправлено: <b>{sent}</b> из <b>{total}</b>"
                )
            except:
                pass

        await asyncio.sleep(0.08)

    try:
        await status_msg.edit_text(
            f"✅ Рассылка завершена!\n"
            f"Отправлено: <b>{sent}</b> из <b>{total}</b>"
        )
    except:
        pass

@router.callback_query(F.data == "bc_personal")
async def bc_personal_start(callback: types.CallbackQuery, state):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(BroadcastStates.personal_id)
    await callback.message.answer("Введите ID пользователя:")
    await callback.answer()

@router.message(BroadcastStates.personal_id)
async def bc_personal_get_id(message: types.Message, state):
    if not message.text.isdigit():
        return await message.answer("❌ Введите корректный ID (число).")

    await state.update_data(user_id=int(message.text))
    await state.set_state(BroadcastStates.personal_text)

    await message.answer("Теперь введите текст сообщения:")

@router.message(BroadcastStates.personal_text)
async def bc_personal_send(message: types.Message, state):
    data = await state.get_data()
    await state.clear()

    user_id = data["user_id"]
    text = message.text

    try:
        await message.bot.send_message(user_id, text)
        await message.answer("✅ Сообщение отправлено.")
    except TelegramForbiddenError:
        await message.answer("❌ Пользователь заблокировал бота.")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
