"""
KinoBot — Telegram kino bot
Texnologiyalar: Python 3.10+, aiogram 3.x, aiosqlite, python-dotenv
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start, movie, admin, ads_admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kinobot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("KinoBot ishga tushmoqda...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin → ads_admin → start → movie
    dp.include_router(admin.router)
    dp.include_router(ads_admin.router)
    dp.include_router(start.router)
    dp.include_router(movie.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling rejimida ishga tushdi.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())

