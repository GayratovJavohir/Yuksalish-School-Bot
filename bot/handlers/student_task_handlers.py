# handlers/student_task_handlers.py
import logging
import time
import tempfile
from fileinput import filename
from pathlib import Path
import os
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from ..states import RoleState
from ..keyboards import get_main_keyboard
from ..services.user_service import UserService
from ..services.task_service import TaskService
from ..bot.utils import download_file_from_telegram # Assuming you'll create a utility for this

student_task_router = Router()
logger = logging.getLogger(__name__)

@student_task_router.message(RoleState.profile_menu, F.text == "Tasks")
async def show_tasks(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role != "student":
        await message.answer("Sizda bu funksiya mavjud emas.")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Task 1", callback_data="task_1")],
        [InlineKeyboardButton(text="Task 2", callback_data="task_2")]
    ])
    await message.answer("Please select a task", reply_markup=markup)
    await state.set_state(RoleState.choosing_task)

@student_task_router.callback_query(RoleState.choosing_task, F.data.startswith("task_"))
async def task_selected(callback: CallbackQuery, state: FSMContext):
    task_name = f"Task {callback.data.split('_')[1]}"
    await state.update_data(selected_task=task_name)
    await callback.message.answer(
        f"Please send a round video (Telegram video message) as your answer for {task_name}."
    )
    await state.set_state(RoleState.waiting_for_task_video)
    await callback.answer()

@student_task_router.message(RoleState.waiting_for_task_video, F.video_note)
async def process_task_video(message: Message, state: FSMContext, bot: Bot):
    user = None
    processing_msg = None

    try:
        if message.forward_from or message.forward_from_chat:
            await message.answer("❌ Forwarded videos are not allowed.")
            return

        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        data = await state.get_data()
        task_name = data.get("selected_task", "Unknown Task")

        if message.video_note.duration > 60:
            await message.answer("⏱️ Video exceeds 1 minute limit")
            return

        if message.video_note.file_size > 20 * 1024 * 1024:  # 20MB
            await message.answer("📦 File too large (max 20MB)")
            return

        processing_msg = await message.answer("🔄 Processing your video...")

        file_id = message.video_note.file_id
        file_bytes_io = await download_file_from_telegram(bot, file_id)
        video_bytes = file_bytes_io.getvalue()
        file_bytes_io.close()

        filename = f"video_{message.from_user.id}_{int(time.time())}.mp4"

        await TaskService.save_video_task_submission(
            student=user,
            task_name=task_name,
            video_bytes=video_bytes,
            filename=filename
        )

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


@student_task_router.message(RoleState.waiting_for_task_video, F.video)
async def process_regular_video(message: Message, state: FSMContext):
    MAX_SIZE_MB = 50
    if message.video.file_size > MAX_SIZE_MB * 1024 * 1024:
        await message.answer(f"❌ Video is too large. Please keep it under {MAX_SIZE_MB}MB")
        return
    await message.answer("Please send a round video message (video note), not a regular video.")


@student_task_router.message(RoleState.waiting_for_task_video)
async def invalid_task_video(message: Message):
    await message.answer("Please send a round video message (video note).")