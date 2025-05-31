import logging
import time
import uuid
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.core.cache import cache
from aiogram.types import BufferedInputFile
from bot.models import CustomUser, Book, StudentTask, ReadingSubmission
from pathlib import Path
import asyncio

from bot.utils import get_books_for_month_and_class

router = Router()
logger = logging.getLogger(__name__)


# --- States ---
class RoleState(StatesGroup):
    choosing_role = State()
    waiting_for_login = State()
    profile_menu = State()
    editing_field = State()
    editing_value = State()
    choosing_task = State()
    waiting_for_task_video = State()
    choosing_month = State()
    choosing_book = State()
    waiting_for_voice_message = State()
    uploading_book_title = State()
    uploading_book_month = State()
    uploading_book_file = State()


# --- Keyboards ---
def get_main_keyboard(user_role):
    if user_role == 'student':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Profile"), KeyboardButton(text="Tasks")],
                [KeyboardButton(text="Reading (Kitobxonlik)")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'coordinator':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Profile"), KeyboardButton(text="📤 Add Book")],
                [KeyboardButton(text="📋 List Books"), KeyboardButton(text="🚫 Cancel")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Profile")]
            ],
            resize_keyboard=True
        )


edit_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Username")],
        [KeyboardButton(text="First name")],
        [KeyboardButton(text="Last name")],
        [KeyboardButton(text="Password")],
        [KeyboardButton(text="Bekor qilish")]
    ],
    resize_keyboard=True
)

parent_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Logout")]
    ],
    resize_keyboard=True
)

profile_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Edit"), KeyboardButton(text="Logout")]
    ],
    resize_keyboard=True
)


# --- Helper Functions ---
async def get_user(telegram_id):
    return await sync_to_async(
        lambda: CustomUser.objects.select_related("branch", "student_class").filter(telegram_id=telegram_id).first()
    )()


async def download_file(bot, file_id):
    """Async function to download Telegram file"""
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        downloaded_bytes = await bot.download_file(file_path)
        return downloaded_bytes
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise


@sync_to_async
def save_video_task(student, task_name, video_bytes, filename):
    """Save video task submission"""
    try:
        submission = StudentTask(student=student, task_name=task_name)
        submission.video_file.save(filename, ContentFile(video_bytes))
        submission.save()
        return submission
    except Exception as e:
        logger.error(f"Error saving video task: {e}")
        raise


@sync_to_async
def save_book(user, title, month, file_bytes, filename):
    """Save book with file"""
    try:
        book = Book(title=title, month=month, uploaded_by=user)
        book.file.save(filename, ContentFile(file_bytes))
        book.save()
        return book
    except Exception as e:
        logger.error(f"Error saving book: {e}")
        raise


@sync_to_async
def get_books_for_month(month):
    """Get books for specific month with caching"""
    cache_key = f"books_{month.lower()}"
    books = cache.get(cache_key)
    if not books:
        books = list(Book.objects.filter(month__iexact=month))
        cache.set(cache_key, books, timeout=60 * 60)
    return books


# --- Common Handlers ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user:
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Student")],
                [KeyboardButton(text="Coordinator")],
                [KeyboardButton(text="Parent")]
            ],
            resize_keyboard=True
        )
        await message.answer("Iltimos, rolingizni tanlang:", reply_markup=keyboard)
        await state.set_state(RoleState.choosing_role)


@router.message(RoleState.choosing_role)
async def role_chosen(message: Message, state: FSMContext):
    role = message.text.lower()
    if role in ["student", "parent", "coordinator"]:
        await state.update_data(selected_role=role)
        await message.answer("Login va parolingizni quyidagicha yuboring:\n`login123 password123`")
        await state.set_state(RoleState.waiting_for_login)
    else:
        await message.answer("Iltimos berilgan rolellardan birini tanlang:")


@router.message(RoleState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    try:
        login, password = message.text.strip().split()
    except ValueError:
        await message.answer("Iltimos, login va parolni quyidagicha kiriting:\n`login123 password123`")
        return

    user = await sync_to_async(authenticate)(username=login, password=password)
    expected_role = (await state.get_data()).get("selected_role")

    if user and user.role == expected_role:
        user.telegram_id = message.from_user.id
        await sync_to_async(user.save)()
        await message.answer(
            f"Xush kelibsiz, {user.username}!",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer("Login yoki parol noto'g'ri yoki rolingiz mos emas. Iltimos, qayta urinib ko'ring.")


@router.message(RoleState.profile_menu)
async def profile_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    if message.text == "Profile":
        profile_text = (
            f"🆔 Username: {user.username}\n"
            f"📛 Ismi: {user.first_name or '---'}\n"
            f"👪 Familiyasi: {user.last_name or '---'}\n"
            f"🏫 Filiali: {user.branch.name if user.branch else '---'}\n"
            f"📚 Sinfi: {user.student_class or '---'}"
        )

        if user.role == "student":
            await message.answer(f"👤 Profil ma'lumotlari:\n{profile_text}", reply_markup=profile_keyboard)
        elif user.role == "parent":
            await message.answer(
                f"👨‍👩‍👦 Sizning farzandingizning ma'lumotlari:\n{profile_text}",
                reply_markup=parent_keyboard
            )
        elif user.role == "coordinator":
            await message.answer(f"🧑‍💼 Koordinator profili:\n{profile_text}", reply_markup=profile_keyboard)

    elif message.text == "Edit":
        if user.role not in ["student", "coordinator"]:
            await message.answer("Faqat student va coordinatorlar o'z profilini tahrir qilishi mumkin.")
            return
        await message.answer("Qaysi ma'lumotni tahrirlamoqchisiz?", reply_markup=edit_keyboard)
        await state.set_state(RoleState.editing_field)

    elif message.text == "Logout":
        user = await get_user(message.from_user.id)
        if user:
            user.telegram_id = None
            await sync_to_async(user.save)()
        await message.answer(
            "Siz tizimdan chiqdingiz.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="/start")]],
                resize_keyboard=True
            )
        )
        await state.clear()

    elif message.text == "Tasks" and user.role == "student":
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Task 1", callback_data="task_1")],
            [InlineKeyboardButton(text="Task 2", callback_data="task_2")]
        ])
        await message.answer("Please select a task", reply_markup=markup)
        await state.set_state(RoleState.choosing_task)

    elif message.text == "Reading (Kitobxonlik)" and user.role == "student":
        current_month = datetime.now().strftime("%B")
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]

        buttons = []
        for month in months:
            btn_text = f"⭐ {month}" if month == current_month else month
            buttons.append(InlineKeyboardButton(text=btn_text, callback_data=f"month_{month}"))

        markup = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 3] for i in range(0, len(buttons), 3)])
        await message.answer(
            "Please select a month (current month is starred):",
            reply_markup=markup
        )
        await state.set_state(RoleState.choosing_month)

    elif message.text == "📤 Add Book" and user.role == "coordinator":
        await message.answer("📖 Enter the book title:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RoleState.uploading_book_title)


    elif message.text == "📋 List Books" and user.role == "coordinator":
        books = await sync_to_async(list)(
            Book.objects.filter(uploaded_by=user).order_by('month', 'title')
        )

        if not books:
            await message.answer("📭 Siz hali hech qanday kitob qo‘shmagansiz.")
            return

        response = ["📚 Qo'shgan kitoblaringiz:"]
        current_month = None

        for book in books:
            if book.month != current_month:
                response.append(f"\n📅 {book.month}:")
                current_month = book.month
            response.append(f"- {book.title} (ID: {book.id})")

        await message.answer("\n".join(response))


# --- Profile Editing Handlers ---
@router.message(RoleState.editing_field)
async def ask_for_new_value(message: Message, state: FSMContext):
    field_map = {
        "Username": "username",
        "First name": "first_name",
        "Last name": "last_name",
        "Password": "password"
    }

    if message.text == "Bekor qilish":
        await message.answer(
            "Tahrirlash bekor qilindi.",
            reply_markup=get_main_keyboard((await get_user(message.from_user.id)).role)
        )
        await state.set_state(RoleState.profile_menu)
        return

    field = field_map.get(message.text)
    if not field:
        await message.answer("Noto'g'ri tanlov. Iltimos, menyudan birini tanlang.")
        return

    await state.update_data(edit_field=field)
    await message.answer(f"Yangi qiymatni kiriting ({message.text}):")
    await state.set_state(RoleState.editing_value)


@router.message(RoleState.editing_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    if field == "password":
        await sync_to_async(user.set_password)(message.text)
    else:
        setattr(user, field, message.text)

    await sync_to_async(user.save)()
    await message.answer("✅ Ma'lumot yangilandi", reply_markup=get_main_keyboard(user.role))
    await state.set_state(RoleState.profile_menu)


# --- Student Task Handlers ---
@router.callback_query(RoleState.choosing_task, F.data.startswith("task_"))
async def task_selected(callback: CallbackQuery, state: FSMContext):
    task_name = f"Task {callback.data.split('_')[1]}"
    await state.update_data(selected_task=task_name)
    await callback.message.answer(
        f"Please send a round video (Telegram video message) as your answer for {task_name}."
    )
    await state.set_state(RoleState.waiting_for_task_video)
    await callback.answer()


@router.message(RoleState.waiting_for_task_video, F.video_note)
async def process_task_video(message: Message, state: FSMContext):
    user = None
    processing_msg = None
    temp_path = None

    try:
        # 1. Basic validations
        if message.forward_from or message.forward_from_chat:
            await message.answer("❌ Forwarded videos are not allowed.")
            return

        # 2. Get user and task data
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=message.from_user.id)
        data = await state.get_data()
        task_name = data.get("selected_task", "Unknown Task")

        # 3. Validate video
        if message.video_note.duration > 60:
            await message.answer("⏱️ Video exceeds 1 minute limit")
            return

        if message.video_note.file_size > 20 * 1024 * 1024:  # 20MB
            await message.answer("📦 File too large (max 20MB)")
            return

        # 4. Start processing
        processing_msg = await message.answer("🔄 Processing your video...")

        # 5. Download file
        file = await message.bot.get_file(message.video_note.file_id)
        temp_dir = Path(tempfile.gettempdir()) / "tg_videos"
        temp_dir.mkdir(exist_ok=True, parents=True)
        temp_path = temp_dir / f"video_{message.from_user.id}_{int(time.time())}.mp4"

        await message.bot.download_file(file.file_path, destination=str(temp_path))

        # 6. Verify download
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise ValueError("Empty video file")

        # 7. Save to database
        with open(temp_path, 'rb') as f:
            video_bytes = f.read()
            await save_video_task(
                student=user,
                task_name=task_name,
                video_bytes=video_bytes,
                filename=temp_path.name
            )

        # 8. Success message
        success_msg = (
            "✅ Video uploaded successfully!\n\n"
            f"📝 Task: {task_name}\n"
            f"⏱ Duration: {message.video_note.duration}s\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        await processing_msg.delete()
        await message.answer(success_msg, reply_markup=get_main_keyboard(user.role))

    except Exception as e:
        logger.error(f"Video upload failed: {e}")

        error_msg = (
            "❌ Upload failed\n\n"
            "Please:\n"
            "1. Check your connection\n"
            "2. Try a shorter video\n"
            "3. Retry in 5 minutes"
        )

        if processing_msg:
            try:
                await processing_msg.delete()
            except:
                pass

        await message.answer(error_msg, reply_markup=get_main_keyboard(user.role if user else None))

    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete temp file: {e}")



@router.message(RoleState.waiting_for_task_video, F.video)
async def process_regular_video(message: Message, state: FSMContext):
    MAX_SIZE_MB = 50
    if message.video.file_size > MAX_SIZE_MB * 1024 * 1024:
        await message.answer(f"❌ Video is too large. Please keep it under {MAX_SIZE_MB}MB")
        return



@router.message(RoleState.waiting_for_task_video)
async def invalid_task_video(message: Message):
    await message.answer("Please send a round video message (video note).")



@sync_to_async
def save_video_task(student, task_name, video_bytes, filename):
    try:
        submission = StudentTask(student=student, task_name=task_name)
        submission.video_file.save(filename, ContentFile(video_bytes))
        submission.save()
        return submission
    except Exception as e:
        logger.error(f"[ERROR] Failed to save video task: {e}")
        raise





# --- Reading Handlers ---
@router.callback_query(RoleState.choosing_month, F.data.startswith("month_"))
async def month_selected(callback: CallbackQuery, state: FSMContext):
    try:
        month = callback.data.split('_')[1]
        user = await get_user(callback.from_user.id)

        if not user.student_class:
            await callback.message.answer("❌ Sizning sinfingiz aniqlanmadi.")
            await state.set_state(RoleState.profile_menu)
            return

        books = await get_books_for_month_and_class(month, user.student_class.id)

        if not books:
            await callback.message.answer(f"❌ {month} oyi uchun hozircha kitoblar mavjud emas.")
            await state.set_state(RoleState.profile_menu)
            return

        buttons = [
            [InlineKeyboardButton(text=f"📚 {book.title}", callback_data=f"book_{book.id}")]
            for book in books
        ]

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer(
            f"📅 {month} oyi uchun {user.student_class} sinfi kitoblari:",
            reply_markup=markup
        )
        await state.set_state(RoleState.choosing_book)
        await callback.answer()

    except Exception as e:
        await callback.message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
        await state.set_state(RoleState.profile_menu)
        await callback.answer()


from aiogram.types import InputFile
from urllib.parse import urljoin
import aiohttp
import tempfile
import os


async def download_file_from_url(url, filename=None):
    """Download file from URL to temporary file"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download file: HTTP {response.status}")

            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    tmp_file.write(chunk)

                tmp_path = tmp_file.name

    return tmp_path



@router.callback_query(RoleState.choosing_book, F.data.startswith("book_"))
async def book_selected(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        book_id = int(callback.data.split('_')[1])
        book = await sync_to_async(Book.objects.get)(id=book_id)

        # Check if file exists using our custom method
        file_exists = await sync_to_async(book.file_exists)()
        if not file_exists:
            await callback.message.answer("❌ Kitob fayli topilmadi. Iltimos, administratorga murojaat qiling.")
            return

        # Check file size
        file_size = await sync_to_async(lambda: book.file.size)()
        if file_size > 50 * 1024 * 1024:
            await callback.message.answer(
                f"❌ Kitob hajmi {file_size // (1024 * 1024)}MB. "
                f"Telegramda maksimum 50MB gacha fayl yuborish mumkin."
            )
            return

        # Read file content in memory
        file_content = await sync_to_async(book.file.read)()
        filename = os.path.basename(book.file.name)

        document = BufferedInputFile(file=file_content, filename=filename)
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=document,
            caption=f"📖 {book.title}\n📅 Oy: {book.month}"
        )

        # Ask for voice confirmation
        await callback.message.answer(
            "🎤 Kitobni o'qiganligingizni tasdiqlash uchun ovozli xabar yuboring",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Bekor qilish")]],
                resize_keyboard=True
            )
        )

        await state.update_data(selected_book_id=book.id)
        await state.set_state(RoleState.waiting_for_voice_message)
        await callback.answer()

    except Exception as e:
        logger.error(f"Book download error. Book ID: {book_id}. Error: {str(e)}")
        await callback.message.answer(
            "❌ Kitob yuklanmadi. Iltimos, keyinroq urunib ko'ring yoki administratorga murojaat qiling."
        )
        await state.set_state(RoleState.profile_menu)
        await callback.answer()


@router.message(RoleState.waiting_for_voice_message, F.voice)
async def process_voice_message(message: Message, state: FSMContext, bot: Bot):
    if message.forward_from or message.forward_from_chat:
        await message.answer("Forwarded voice messages are not allowed. Please record your own.")
        return

    try:
        data = await state.get_data()
        user = await get_user(message.from_user.id)
        book = await sync_to_async(Book.objects.get)(id=data['selected_book_id'])

        # Download the voice file
        file_bytes = await download_file(bot, message.voice.file_id)
        filename = f"voice_{uuid.uuid4()}.ogg"

        # Create the submission
        submission = ReadingSubmission(
            student=user,
            month=data['selected_month'],
            book=book,
            voice_message_id=message.voice.file_id
        )

        # Save voice file (async-safe)
        await sync_to_async(submission.voice_file.save)(filename, ContentFile(file_bytes.read()))

        # Save submission itself (async-safe)
        await sync_to_async(submission.save)()

        await message.answer(
            "✅ Sizning kitob o'qishingiz qabul qilindi!",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)

    except Exception as e:
        logger.error(f"Error saving voice submission: {str(e)}")
        await message.answer(
            "❌ Ovozli xabar saqlanmadi. Iltimos, qayta urunib ko'ring.",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)



@router.message(RoleState.waiting_for_voice_message)
async def invalid_voice_message(message: Message):
    await message.answer("Please send a voice message.")


# --- Coordinator Book Upload Handlers ---
@router.message(RoleState.uploading_book_title)
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


@router.callback_query(RoleState.uploading_book_month, F.data.startswith("bookmonth_"))
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


@router.message(RoleState.uploading_book_file, F.document)
async def process_book_file(message: Message, state: FSMContext):
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
        user = await get_user(message.from_user.id)
        file_bytes = await download_file(message.bot, message.document.file_id)
        filename = f"{uuid.uuid4()}_{message.document.file_name}"

        await save_book(
            user=user,
            title=data['book_title'],
            month=data['book_month'],
            file_bytes=file_bytes.read(),
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


@router.message(
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


# --- Help Command ---
@router.message(Command('help'))
async def handle_help(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return

    if user.role == 'coordinator':
        help_text = (
            "📚 <b>Coordinator Commands</b>\n\n"
            "/book - Manage books\n"
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



