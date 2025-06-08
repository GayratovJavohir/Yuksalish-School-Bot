# handlers/student_reading_handlers.py
import logging
import os
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from ..models import Book, CustomBook
from ..states import RoleState
from ..keyboards import get_main_keyboard
from ..services.user_service import UserService
from ..services.book_service import BookService
from ..services.reading_service import ReadingService
from ..bot.utils import download_file_from_telegram
import asyncio

student_reading_router = Router()
logger = logging.getLogger(__name__)

@student_reading_router.message(RoleState.profile_menu, F.text == "Reading (Kitobxonlik)")
async def show_reading_months(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role != "student":
        await message.answer("Sizda bu funksiya mavjud emas.")
        return

    current_month = datetime.now().strftime("%B")
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    buttons = []
    for month in months:
        buttons.append([InlineKeyboardButton(text=month, callback_data=f"month_{month}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📚 Iltimos, kitob o'qish oyini tanlang:", reply_markup=keyboard)
    await state.set_state(RoleState.choosing_month)


@student_reading_router.callback_query(RoleState.choosing_month, F.data.startswith("month_"))
async def month_selected(callback: CallbackQuery, state: FSMContext):
    month = callback.data.split('_')[1]
    await state.update_data(selected_month=month)

    books = await BookService.get_books_by_month(month)
    if not books:
        await callback.message.answer("Bu oy uchun kitoblar topilmadi.")
        await callback.answer()
        return

    buttons = []
    for book in books:
        buttons.append([InlineKeyboardButton(text=book.title, callback_data=f"book_{book.id}")])

    buttons.append([InlineKeyboardButton(text="Boshqa kitob", callback_data="other_book")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(
        f"📖 '{month}' oyi uchun kitobni tanlang:",
        reply_markup=keyboard
    )
    await state.set_state(RoleState.choosing_book)
    await callback.answer()


@student_reading_router.callback_query(RoleState.choosing_book, F.data.startswith("book_"))
async def book_selected(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        book_id = int(callback.data.split('_')[1])
        book = await BookService.get_book_by_id(book_id)

        if not book:
            await callback.message.answer("Kitob topilmadi.")
            await callback.answer()
            return

        # Check if the book file exists
        if not book.file or not await sync_to_async(os.path.exists)(book.file.path):
            await callback.message.answer("Kitob fayli topilmadi. Iltimos, admin bilan bog'laning.")
            await callback.answer()
            return

        # Check file size before sending
        file_size_bytes = await sync_to_async(lambda: book.file.size)()
        if file_size_bytes > 50 * 1024 * 1024: # 50 MB limit for Telegram documents
            await callback.message.answer(
                f"❌ Fayl hajmi juda katta ({file_size_bytes / (1024 * 1024):.2f}MB). "
                f"Telegramda maksimum 50MB gacha fayl yuborish mumkin."
            )
            await callback.answer()
            return

        # Fayl kontentini o'qish va yuborish
        file_content = await sync_to_async(book.file.read)()
        filename = os.path.basename(book.file.name)

        document = BufferedInputFile(file=file_content, filename=filename)
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=document,
            caption=f"📖 {book.title}\n📅 Oy: {book.month}"
        )

        # Kitob yuborilgandan so'ng, ovozli xabar so'rash
        await callback.message.answer(
            "🎙 Iltimos, kitobingizdan o'qigan qismingizni ovozli xabar qilib yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Bekor qilish")]],
                resize_keyboard=True
            )
        )

        # Holatni o'zgartirish va tanlangan kitob ID'sini saqlash
        await state.update_data(selected_book_id=book.id)
        await state.set_state(RoleState.waiting_for_voice_message)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in book_selected handler: {str(e)}", exc_info=True)
        await callback.message.answer("❌ Kitobni yuborishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await callback.answer()
        await state.set_state(RoleState.profile_menu) # Add fallback state


@student_reading_router.message(RoleState.waiting_for_custom_book_name)
async def custom_book_name_received(message: Message, state: FSMContext):
    if message.text == "Bekor qilish":
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard('student'))
        await state.set_state(RoleState.profile_menu)
        return

    custom_book_name = message.text
    await state.update_data(custom_book_name=custom_book_name)

    await message.answer(
        "🎙 Iltimos, o'qigan kitobingizdan ovozli xabar yuboring.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Bekor qilish")]],
            resize_keyboard=True
        )
    )
    await state.set_state(RoleState.waiting_for_voice_message)


@student_reading_router.message(RoleState.waiting_for_voice_message, F.voice)
async def voice_message_received(message: Message, state: FSMContext, bot: Bot):
    try:
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        if not user or user.role != "student":
            await message.answer("Sizda bu funksiya mavjud emas.")
            return

        data = await state.get_data()
        selected_month = data.get('selected_month')
        selected_book_id = data.get('selected_book_id')
        custom_book_name = data.get('custom_book_name')

        if not selected_month:
            await message.answer("Oy tanlanmagan. Iltimos, qaytadan boshlang.", reply_markup=get_main_keyboard('student'))
            await state.clear()
            return

        book = None
        custom_book = None
        if selected_book_id:
            book = await BookService.get_book_by_id(selected_book_id)
            if not book:
                await message.answer("Tanlangan kitob topilmadi. Iltimos, qaytadan boshlang.", reply_markup=get_main_keyboard('student'))
                await state.clear()
                return
        elif custom_book_name:
            custom_book, created = await sync_to_async(CustomBook.objects.get_or_create)(
                name=custom_book_name, defaults={'student': user} # Assuming student is needed for CustomBook creation
            )
        else:
            await message.answer("Kitob tanlanmagan. Iltimos, qaytadan boshlang.", reply_markup=get_main_keyboard('student'))
            await state.clear()
            return

        voice_file_id = message.voice.file_id
        file_info = await bot.get_file(voice_file_id)
        file_path = file_info.file_path

        # Download voice file
        downloaded_file = await download_file_from_telegram(bot, file_path)
        if not downloaded_file:
            await message.answer("❌ Ovozli xabar yuklab olinmadi. Iltimos, qaytadan urinib ko'ring.")
            return

        submission = await ReadingService.create_reading_submission(
            student=user,
            month=selected_month,
            voice_message_id=voice_file_id,
            book=book,
            custom_book=custom_book
        )

        filename = f"{submission.id}_{message.voice.file_unique_id}.ogg"
        await ReadingService.save_submission_voice_file(submission, filename, downloaded_file)

        await message.answer(
            "Rahmat! Endi o'qigan kitobingizdagi betlar sonini raqamda yuboring (masalan: 45).",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Bekor qilish")]],
                resize_keyboard=True
            )
        )
        await state.update_data(current_submission_id=submission.id)
        await state.set_state(RoleState.waiting_for_page_count)

    except Exception as e:
        logger.error(f"Error processing voice message: {str(e)}", exc_info=True)
        await message.answer("❌ Ovozli xabarni qabul qilishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await state.set_state(RoleState.profile_menu) # Fallback to profile menu on error

@student_reading_router.message(RoleState.waiting_for_page_count, F.text.regexp(r'^\d+$'))
async def page_count_received(message: Message, state: FSMContext):
    try:
        page_count = int(message.text)
        data = await state.get_data()
        submission_id = data.get('current_submission_id')

        if not submission_id:
            await message.answer("Xatolik: topshirish ID topilmadi. Iltimos, qaytadan boshlang.", reply_markup=get_main_keyboard('student'))
            await state.clear()
            return

        await ReadingService.update_submission_page_count(submission_id, page_count)

        await message.answer(
            f"✅ Sizning {page_count} bet kitob o'qishingiz muvaffaqiyatli qayd etildi!",
            reply_markup=get_main_keyboard('student')
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error saving page count: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Xatolik yuz berdi. Iltimos, faqat raqam yuboring (masalan: 45).",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Bekor qilish")]],\
                resize_keyboard=True
            )
        )

@student_reading_router.message(RoleState.waiting_for_page_count)
async def invalid_page_count(message: Message, state: FSMContext):
    if message.text == "Bekor qilish":
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard('student'))
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer("Iltimos, faqat raqam yuboring (masalan: 45)")

@student_reading_router.message(RoleState.waiting_for_voice_message)
async def invalid_voice_message(message: Message):
    await message.answer("Please send a voice message.")


@student_reading_router.callback_query(RoleState.choosing_book, F.data == "other_book")
async def other_book_selected(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer(
            "📖 Iltimos, o'qigan kitobingiz nomini yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Bekor qilish")]],
                resize_keyboard=True
            )
        )
        await state.set_state(RoleState.waiting_for_custom_book_name)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in other_book_selected handler: {str(e)}", exc_info=True)
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await callback.answer()
        await state.set_state(RoleState.profile_menu) # Fallback to profile menu on error