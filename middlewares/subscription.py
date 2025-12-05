from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import BaseMiddleware

from database.db import get_db
from config import ADMINS


def subscription_kb(channels):
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for ch in channels:
        title = ch["title"] or ch["username"]
        username = ch["username"]
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"➡ {title}",
                url=f"https://t.me/{username}"
            )
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(
            text="🔄 Проверить подписку",
            callback_data="check_subs"
        )
    ])

    return kb


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):

        flags = getattr(getattr(handler, "callback", handler), "flags", {})
        if flags.get("allow_without_subscription"):
            return await handler(event, data)

        user_id = event.from_user.id
        bot = data["bot"]

        db = await get_db()
        cur = await db.execute("SELECT channel_id, username, title FROM required_channels")
        channels = await cur.fetchall()
        await db.close()

        if not channels:
            return await handler(event, data)

        subscribed = True

        if user_id in ADMINS:
            return await handler(event, data)
        for ch in channels:
            channel_id = ch["channel_id"]
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
            return await handler(event, data)

        kb = subscription_kb(channels)

        try:
            await event.answer(
                "❗ Для пользования ботом требуется подписка на каналы.",
                reply_markup=kb
            )
        except Exception:
            await event.message.answer(
                "❗ Для пользования ботом требуется подписка на каналы.",
                reply_markup=kb
            )

        return
