# handlers/common_handlers.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from ..services.user_service import UserService

common_router = Router()

@common_router.message(Command('help'))
async def handle_help(message: Message):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    if user.role == 'coordinator':
        help_text = (
            "📚 <b>Coordinator Commands</b>\n\n"
            "/book - Manage books\n" # Bu commandni keyinroq qo'shish kerak bo'ladi
            "Add Book - Upload new books\n"
            "List Books - View existing books\n"
            "/help - Show this help"
        )
    elif user.role == 'student':
        help_text = (
            "📖 <b>Student Commands</b>\n\n"
            "Reading - Access books\n"
            "Tasks - Submit video tasks\n"
            "/help - Show this help"
        )
    else:
        help_text = "Available commands: /help"

    await message.answer(help_text, parse_mode="HTML")