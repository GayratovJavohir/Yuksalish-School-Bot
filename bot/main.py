# main.py (yoki botni ishga tushiradigan asosiy fayl)
import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.utils.telegram import BOT_TOKEN
# Import routers from handlers
from handlers.start_handlers import start_router
from handlers.profile_handlers import profile_router
from handlers.student_task_handlers import student_task_router
from handlers.student_reading_handlers import student_reading_router
from handlers.coordinator_book_handlers import coordinator_book_router
from handlers.common_handlers import common_router

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register all routers
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(student_task_router)
    dp.include_router(student_reading_router)
    dp.include_router(coordinator_book_router)
    dp.include_router(common_router)

    logging.basicConfig(level=logging.INFO) # Basic logging setup

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())