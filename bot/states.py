# states.py
from aiogram.fsm.state import StatesGroup, State

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
    waiting_for_custom_book_name = State()
    waiting_for_page_count = State()