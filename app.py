import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN


from handlers.start import router as start_router
from handlers.deposit import router as deposit_router
from handlers.withdraw import router as withdraw_router
from handlers.staking import router as staking_router
from handlers.tasks import router as tasks_router
from handlers.restrictred import router as restricted_router
from handlers.subscription import router as subscription_router

from handlers.admin import router as admin_router
from handlers.admin_finance import router as admin_finance_router
from handlers.admin_tasks import router as admin_tasks_router
from handlers.admin_broadcast import router as admin_broadcast_router
from handlers.admin_promos import router as admin_promos_router


from middlewares.maintenance import MaintenanceMiddleware
from middlewares.ban import BanMiddleware
from middlewares.subscription import SubscriptionMiddleware
from middlewares.admin import AdminMiddleware

from aiogram.fsm.storage.memory import MemoryStorage


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    admin_router.include_router(admin_finance_router)
    admin_router.include_router(admin_tasks_router)
    admin_router.include_router(admin_broadcast_router)
    admin_router.include_router(admin_promos_router)
    dp.include_router(admin_router)

    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())


    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())


    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())







    dp.include_router(start_router)
    dp.include_router(subscription_router)

    dp.include_router(restricted_router)
    dp.include_router(deposit_router)
    dp.include_router(withdraw_router)
    dp.include_router(staking_router)
    dp.include_router(tasks_router)

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
