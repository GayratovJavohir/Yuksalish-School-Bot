# handlers/coordinator_book_handlers.py
import logging
import uuid
import os
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import or_f

from ..bot.utils import download_file_from_telegram
from ..states import RoleState
from ..keyboards import get_main_keyboard
from ..services.user_service import UserService
from ..services.book_service import BookService

coordinator_book_router = Router()
logger = logging.getLogger(__name__)

@coordinator_book_router.message(RoleState.profile_menu, F.text == "📤 Add Book")
async def add_book_start(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role != "coordinator":
        await message.answer("Sizda bu funksiya mavjud emas.")
        return
    await message.answer("📖 Enter the book title:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RoleState.uploading_book_title)

@coordinator_book_router.message(RoleState.uploading_book_title)
async def process_book_title(message: Message, state: FSMContext):
    if len(message.text) > 200:
        await message.answer("Title too long (max 200 characters). Please try again.")
        return

    await state.update_data(book_title=message.text)

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    buttons = [InlineKeyboardButton(text=month, callback_data=f"bookmonth_{month}") for month in months]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 3] for i in range(0, len(buttons), 3)])

    await message.answer("📅 Select the month for this book:", reply_markup=markup)
    await state.set_state(RoleState.uploading_book_month)

@coordinator_book_router.callback_query(RoleState.uploading_book_month, F.data.startswith("bookmonth_"))
async def process_book_month(callback: CallbackQuery, state: FSMContext):
    month = callback.data.split('_')[1]
    await state.update_data(book_month=month)
    await callback.message.answer(
        "📤 Please upload the book file (PDF or Word):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🚫 Cancel")]],
            resize_keyboard=True
        )
    )
    await state.set_state(RoleState.uploading_book_file)
    await callback.answer()

@coordinator_book_router.message(RoleState.uploading_book_file, F.document)
async def process_book_file(message: Message, state: FSMContext, bot: Bot):
    ALLOWED_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    if message.document.mime_type not in ALLOWED_TYPES:
        await message.answer("❌ Only PDF or Word documents are allowed")
        return

    try:
        data = await state.get_data()
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        file_bytes_io = await download_file_from_telegram(bot, message.document.file_id)
        filename = f"{uuid.uuid4()}_{message.document.file_name}"

        await BookService.save_book(
            user=user,
            title=data['book_title'],
            month=data['book_month'],
            file_bytes=file_bytes_io.read(),
            filename=filename
        )

        await message.answer(
            f"✅ Book '{data['book_title']}' uploaded successfully!",
            reply_markup=get_main_keyboard('coordinator')
        )
        await state.set_state(RoleState.profile_menu)

    except Exception as e:
        logger.error(f"Book upload error: {str(e)}")
        await message.answer(
            "❌ Failed to upload book. Please try again.",
            reply_markup=get_main_keyboard('coordinator')
        )
        await state.set_state(RoleState.profile_menu)

@coordinator_book_router.message(RoleState.profile_menu, F.text == "📋 List Books")
async def list_books(message: Message):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role != "coordinator":
        await message.answer("Sizda bu funksiya mavjud emas.")
        return

    books = await BookService.get_all_books_ordered()

    if not books:
        await message.answer("No books available yet.")
        return

    response = ["📚 Available Books:"]
    current_month = None

    for book in books:
        if book.month != current_month:
            response.append(f"\n📅 {book.month}:")
            current_month = book.month
        response.append(f"- {book.title} (ID: {book.id})")

    await message.answer("\n".join(response))

@coordinator_book_router.message(
    or_f(
        RoleState.uploading_book_title,
        RoleState.uploading_book_month,
        RoleState.uploading_book_file
    ),
    F.text == "🚫 Cancel"
)
async def cancel_book_upload(message: Message, state: FSMContext):
    await message.answer(
        "Book upload cancelled",
        reply_markup=get_main_keyboard('coordinator')
    )
    await state.set_state(RoleState.profile_menu)