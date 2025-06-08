# handlers/profile_handlers.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from ..states import RoleState
from ..keyboards import get_main_keyboard, profile_keyboard, parent_keyboard, edit_keyboard
from ..services.user_service import UserService

profile_router = Router()

@profile_router.message(RoleState.profile_menu, F.text == "Profile")
async def show_profile(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    profile_text = (
        f"🆔 Username: {user.username}\n"
        f"📛 Ismi: {user.first_name or '---'}\n"
        f"👪 Familiyasi: {user.last_name or '---'}\n"
        f"🏫 Filiali: {user.branch or '---'}\n"
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

@profile_router.message(RoleState.profile_menu, F.text == "Edit")
async def edit_profile_start(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role not in ["student", "coordinator"]:
        await message.answer("Faqat student va coordinatorlar o'z profilini tahrir qilishi mumkin.")
        return
    await message.answer("Qaysi ma'lumotni tahrirlamoqchisiz?", reply_markup=edit_keyboard)
    await state.set_state(RoleState.editing_field)

@profile_router.message(RoleState.editing_field)
async def ask_for_new_value(message: Message, state: FSMContext):
    field_map = {
        "Username": "username",
        "First name": "first_name",
        "Last name": "last_name",
        "Password": "password"
    }

    if message.text == "Bekor qilish":
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        await message.answer(
            "Tahrirlash bekor qilindi.",
            reply_markup=get_main_keyboard(user.role)
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

@profile_router.message(RoleState.editing_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    user = await UserService.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    if field == "password":
        await UserService.set_user_password(user, message.text)
    else:
        await UserService.update_user_field(user, field, message.text)

    await message.answer("✅ Ma'lumot yangilandi", reply_markup=get_main_keyboard(user.role))
    await state.set_state(RoleState.profile_menu)

@profile_router.message(RoleState.profile_menu, F.text == "Logout")
async def logout_user(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if user:
        user.telegram_id = None
        await UserService.save_user(user)
    await message.answer(
        "Siz tizimdan chiqdingiz.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/start")]],
            resize_keyboard=True
        )
    )
    await state.clear()