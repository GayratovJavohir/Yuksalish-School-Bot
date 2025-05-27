# bot/telegram_bot.py
from aiogram import Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout
from bot.bot_instance import bot
from bot.handlers.handlers import router as main_router
from bot.handlers.tasks import router as task_router

timeout = ClientTimeout(total=30)
session = AiohttpSession(timeout=timeout)

dp = Dispatcher()
dp.include_router(task_router)
dp.include_router(main_router)

async def main():
    print("Bot is starting...")
    await dp.start_polling(bot)
    print("Bot has stopped.")