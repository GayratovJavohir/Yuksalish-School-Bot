from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate

router = Router()

class RoleState(StatesGroup):
    choosing_role = State()
    waiting_for_login = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
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

    if role == "student":
        await message.answer("Login va parolingizni quyidagicha yuboring:\n`login123 password123`")
        await state.set_state(RoleState.waiting_for_login)
    else:
        await message.answer("Hozircha faqat Student roli ishlaydi.")


@router.message(RoleState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    try:
        login, password = message.text.strip().split()
    except ValueError:
        await message.answer("Iltimos, login va parolni quyidagicha kiriting:\n`login123 password123`")
        return

    user = await sync_to_async(authenticate)(username=login, password=password)
    if user and user.role == "student":
        await message.answer(f"Xush kelibsiz, {user.username}!")
        await state.clear()
    else:
        await message.answer("Login yoki parol noto‘g‘ri. Iltimos, qayta urinib ko‘ring.")
