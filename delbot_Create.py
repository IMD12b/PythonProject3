# delbot_Create.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, PROXY_URL
import logging
from handlers.start import start_router
from handlers.courier import courier_orders_router, courier_shifts_router
from handlers.dispatcher import (
    dispatcher_orders_router,
    dispatcher_couriers_router,
    dispatcher_shifts_router,
)
from handlers.moderator import (
    mod_applications_router,
    mod_couriers_router,
    mod_dispatchers_router,
    mod_shifts_router,
    mod_stats_router,
)

from db.database import init_db          # ← ДОБАВИТЬ


async def main():
    await init_db()                    # ← ДОБАВИТЬ

    session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("bot")

    dp.include_router(start_router)
    dp.include_router(courier_orders_router)
    dp.include_router(courier_shifts_router)
    dp.include_router(dispatcher_orders_router)
    dp.include_router(dispatcher_couriers_router)
    dp.include_router(dispatcher_shifts_router)
    dp.include_router(mod_applications_router)
    dp.include_router(mod_couriers_router)
    dp.include_router(mod_dispatchers_router)
    dp.include_router(mod_shifts_router)
    dp.include_router(mod_stats_router)

    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())