# handlers/start_handlers.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from ..states import RoleState
from ..keyboards import get_main_keyboard
from ..services.user_service import UserService
from ..keyboards import start

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await UserService.get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer(
            "Iltimos, rolingizni tanlang:",
            reply_markup=start
        )
        await state.set_state(RoleState.choosing_role)

@start_router.message(RoleState.choosing_role)
async def role_chosen(message: Message, state: FSMContext):
    role = message.text.lower()
    if role in ["student", "parent", "coordinator"]:
        await state.update_data(selected_role=role)
        await message.answer("Login va parolingizni quyidagicha yuboring:\n`login123 password123`")
        await state.set_state(RoleState.waiting_for_login)
    else:
        await message.answer("Iltimos berilgan rolellardan birini tanlang:")

@start_router.message(RoleState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    try:
        login, password = message.text.strip().split()
    except ValueError:
        await message.answer("Iltimos, login va parolni quyidagicha kiriting:\n`login123 password123`")
        return

    user = await UserService.authenticate_user(username=login, password=password)
    expected_role = (await state.get_data()).get("selected_role")

    if user and user.role == expected_role:
        user.telegram_id = message.from_user.id
        await UserService.save_user(user)
        await message.answer(
            f"Xush kelibsiz, {user.username}!",
            reply_markup=get_main_keyboard(user.role)
        )
        await state.set_state(RoleState.profile_menu)
    else:
        await message.answer("Login yoki parol noto'g'ri yoki rolingiz mos emas. Iltimos, qayta urinib ko'ring.")