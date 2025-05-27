from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile

from ..models import CustomUser, TaskSubmission
from ..states import RoleState
from ..keyboards import get_main_keyboard

router = Router()

# Vazifalar uchun inline klaviatura
task_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Yugurish", callback_data="task_Yugurish")],
        [InlineKeyboardButton(text="Mashqlar", callback_data="task_Mashqlar")],
    ]
)


@router.message(F.text.casefold() == "vazifalar")
async def show_tasks(message: Message, state: FSMContext):
    # Foydalanuvchi tizimga kirganligini tekshiramiz
    user = await sync_to_async(CustomUser.objects.filter(telegram_id=message.from_user.id).first)()
    if not user:
        await message.answer("Iltimos, avval tizimga kiring!")
        return

    await state.set_state(RoleState.profile_menu)
    await message.answer("Quyidagi vazifalardan birini tanlang:", reply_markup=task_keyboard)


@router.callback_query(F.data.startswith("task_"))
async def handle_task_selection(callback: CallbackQuery, state: FSMContext):
    task_name = callback.data.split("_", 1)[1]
    await state.update_data(selected_task=task_name)
    await callback.message.answer(
        f"Siz '{task_name}' vazifasini tanladingiz.\n"
        "Iltimos, do'maloq video yuboring (forward qilingan videolar qabul qilinmaydi)."
    )
    await callback.answer()


@router.message(F.video_note)
async def handle_video_note(message: Message, state: FSMContext):
    # Forward qilingan videolarni tekshiramiz
    if message.forward_from or message.forward_from_chat:
        await message.answer("⚠️ Iltimos, forward qilingan videolarni yubormang! Shaxsiy video yuboring.")
        return

    data = await state.get_data()
    task_name = data.get("selected_task")

    if not task_name:
        await message.answer("Iltimos, avval vazifani tanlang!")
        return

    try:
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=message.from_user.id)
        video_note = message.video_note

        # Video hajmini tekshiramiz (masalan, 20MB dan katta bo'lmasin)
        if video_note.file_size > 20 * 1024 * 1024:
            await message.answer("⚠️ Video hajmi juda katta (maksimal 20MB)")
            return

        file = await message.bot.get_file(video_note.file_id)
        file_bytes = await message.bot.download_file(file.file_path)

        django_file = ContentFile(
            file_bytes.read(),
            name=f"{message.from_user.id}_{video_note.file_unique_id}.mp4"
        )

        await sync_to_async(TaskSubmission.objects.create)(
            user=user,
            task_name=task_name,
            video=django_file
        )
        await message.answer("✅ Video muvaffaqiyatli yuborildi! Rahmat!")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}\nIltimos qayta urinib ko'ring.")