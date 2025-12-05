from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import ADMINS
from services.tech_service import TechService

class MaintenanceMiddleware(BaseMiddleware):

    async def __call__(self, handler, event, data):

        mode = await TechService.get_mode()


        if not mode:
            return await handler(event, data)


        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        else:
            return


        if user_id in ADMINS:
            return await handler(event, data)


        if isinstance(event, Message):
            return await event.answer(
                "🛠 <b>Технічні роботи</b>\n"
                "Бот тимчасово недоступний.\n"
                "Спробуйте пізніше.",
                parse_mode="HTML"
            )

        if isinstance(event, CallbackQuery):
            return await event.answer(
                "🛠 Бот недоступний через технічні роботи.",
                show_alert=True
            )
