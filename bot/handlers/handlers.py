import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolbot.settings")
django.setup()

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate

from ..models import CustomUser
from ..states import RoleState
from ..keyboards import (
    get_main_keyboard,
    get_edit_keyboard,
    get_parent_keyboard,
    get_profile_keyboard,
    get_role_selection_keyboard,
    get_start_keyboard
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await sync_to_async(CustomUser.objects.filter(telegram_id=message.from_user.id).first)()
    if user:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz.", reply_markup=get_main_keyboard())
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer(
            "Iltimos, rolingizni tanlang:",
            reply_markup=get_role_selection_keyboard()
        )
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
        await message.answer(f"Xush kelibsiz, {user.username}!", reply_markup=get_main_keyboard())
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer("Login yoki parol noto'g'ri yoki rolingiz mos emas. Iltimos, qayta urinib ko'ring.")


@router.message(RoleState.profile_menu)
async def profile_menu(message: Message, state: FSMContext):
    user = await sync_to_async(CustomUser.objects.filter(telegram_id=message.from_user.id).first)()
    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    if message.text == "Profile":
        profile_text = (
            f"🆔 Username: {user.username}\n"
            f"📛 Ismi: {user.first_name or '---'}\n"
            f"👪 Familiyasi: {user.last_name or '---'}\n"
            f"🏫 Filiali: {user.branch or '---'}\n"
            f"📚 Sinfi: {user.student_class or '---'}"
        )

        if user.role == "student":
            await message.answer(
                f"👤 Profil ma'lumotlari:\n{profile_text}",
                reply_markup=get_profile_keyboard()
            )
        elif user.role == "parent":
            await message.answer(
                f"👨‍👩‍👦 Sizning farzandingizning ma'lumotlari:\n{profile_text}",
                reply_markup=get_parent_keyboard()
            )
        elif user.role == "coordinator":
            await message.answer(
                f"🧑‍💼 Koordinator profili:\n{profile_text}",
                reply_markup=get_profile_keyboard()
            )

    elif message.text == "Edit":
        if user.role not in ["student", "coordinator"]:
            await message.answer("Faqat student va coordinatorlar o'z profilini tahrir qilishi mumkin.")
            return
        await message.answer(
            "Qaysi ma'lumotni tahrirlamoqchisiz?",
            reply_markup=get_edit_keyboard()
        )
        await state.set_state(RoleState.editing_field)

    elif message.text == "Logout":
        if user:
            user.telegram_id = None
            await sync_to_async(user.save)()
        await message.answer(
            "Siz tizimdan chiqdingiz.",
            reply_markup=get_start_keyboard()
        )
        await state.clear()


@router.message(RoleState.editing_field)
async def ask_for_new_value(message: Message, state: FSMContext):
    field_map = {
        "Username": "username",
        "First name": "first_name",
        "Last name": "last_name",
        "Password": "password"
    }

    if message.text == "Bekor qilish":
        await message.answer("Tahrirlash bekor qilindi.", reply_markup=get_main_keyboard())
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
    user = await sync_to_async(CustomUser.objects.filter(telegram_id=message.from_user.id).first)()

    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    if field == "password":
        await sync_to_async(user.set_password)(message.text)
    else:
        setattr(user, field, message.text)

    await sync_to_async(user.save)()
    await message.answer("✅ Ma'lumot yangilandi", reply_markup=get_main_keyboard())
    await state.set_state(RoleState.profile_menu)