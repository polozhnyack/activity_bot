from aiogram.fsm.state import State, StatesGroup


class MainMenu(StatesGroup):
    start_user = State()