from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Vazifalar"), KeyboardButton(text="Profile")],
        ],
        resize_keyboard=True
    )

def get_edit_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Username"), KeyboardButton(text="First name")],
            [KeyboardButton(text="Last name"), KeyboardButton(text="Password")],
            [KeyboardButton(text="Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_parent_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Logout")]
        ],
        resize_keyboard=True
    )

def get_profile_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Edit"), KeyboardButton(text="Logout")]
        ],
        resize_keyboard=True
    )

def get_role_selection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Student")],
            [KeyboardButton(text="Coordinator")],
            [KeyboardButton(text="Parent")]
        ],
        resize_keyboard=True
    )

def get_start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/start")]],
        resize_keyboard=True
    )