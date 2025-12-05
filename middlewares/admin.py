from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any
from aiogram.types import Message, CallbackQuery

from config import ADMINS


class AdminMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable,
            event,
            data: Dict[str, Any]
    ):

        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id


        if user_id in ADMINS:
            return await handler(event, data)


        if isinstance(event, Message):
            return await event.answer("❌ У вас нет доступа к админ-панели.")
        elif isinstance(event, CallbackQuery):
            return await event.answer("❌ Нет доступа.", show_alert=True)
        return None