from aiogram.fsm.state import State, StatesGroup



class ParentRegistration(StatesGroup):
    input_code = State()

class ChildInfo(StatesGroup):
    start_info = State()
    select_month = State()