from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import ADMINS
from services.user_service import UserService

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):


        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        else:
            return await handler(event, data)


        if user_id in ADMINS:
            return await handler(event, data)


        user = await UserService.get_user(user_id)

        if user and user["is_banned"]:

            if isinstance(event, Message):
                return await event.answer("🚫 Вы заблокированы.")
            else:
                return await event.answer("🚫 Вы заблокированы.", show_alert=True)


        return await handler(event, data)
