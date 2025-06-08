# keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)

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

start = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Student")],
        [KeyboardButton(text="Coordinator")],
        [KeyboardButton(text="Parent")]
    ],
    resize_keyboard=True
)

profile_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Edit"), KeyboardButton(text="Logout")]
    ],
    resize_keyboard=True
)

