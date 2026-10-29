# delbot_Create.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, PROXY_URL
import logging
from handlers.start import start_router
from handlers.courier import courier_router
from handlers.dispet import dispet_router
from handlers.moderator import moderator_router

from database.database import init_db          # ← ДОБАВИТЬ


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
    dp.include_router(courier_router)
    dp.include_router(dispet_router)
    dp.include_router(moderator_router)

    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())