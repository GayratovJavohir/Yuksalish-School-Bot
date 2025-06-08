# bot/telegram_bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.handlers.start_handlers import start_router as start_router
from bot.handlers.profile_handlers import profile_router as profile_router
from bot.handlers.student_task_handlers import student_task_router as student_task_router
from bot.handlers.student_reading_handlers import student_reading_router as student_reading_router
from bot.handlers.coordinator_book_handlers import coordinator_book_router as coordinator_book_router
from bot.handlers.common_handlers import common_router as common_router
from bot.utils.telegram import BOT_TOKEN

logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Barcha routerlarni Dispatcher ga qo'shamiz
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(student_task_router)
    dp.include_router(student_reading_router)
    dp.include_router(coordinator_book_router)
    dp.include_router(common_router)

    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())