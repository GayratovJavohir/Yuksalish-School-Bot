from aiogram.fsm.state import StatesGroup, State

class RoleState(StatesGroup):
    choosing_role = State()
    waiting_for_login = State()
    profile_menu = State()
    editing_field = State()
    editing_value = State()