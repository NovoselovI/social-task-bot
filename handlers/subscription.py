from aiogram import Router, types, F
from aiogram.enums.chat_member_status import ChatMemberStatus

from database.db import get_db
from utils.permissions import allow_without_subscription

router = Router()


@allow_without_subscription
@router.callback_query(F.data == "check_subs")
async def check_subs(cb: types.CallbackQuery):

    bot = cb.message.bot
    user_id = cb.from_user.id

    db = await get_db()
    cur = await db.execute("SELECT channel_id, username FROM required_channels")
    rows = await cur.fetchall()
    await db.close()

    subscribed = True

    for row in rows:
        channel_id = row["channel_id"]

        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
            ):
                subscribed = False
                break
        except Exception:
            subscribed = False
            break

    if subscribed:
        try:
            await cb.message.delete()
        except:
            pass

        await cb.answer("✔ Подписка подтверждена!", show_alert=True)

        from keyboards.main_menu import main_menu
        await cb.message.answer(
            "🎉 Подписка подтверждена!\nВы можете пользоваться ботом.",
            reply_markup=main_menu
        )
    else:
        await cb.answer("❌ Вы ещё не подписались!", show_alert=True)
