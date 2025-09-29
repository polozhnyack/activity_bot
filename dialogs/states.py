from aiogram.fsm.state import State, StatesGroup



class ParentRegistration(StatesGroup):
    input_code = State()

class ChildInfo(StatesGroup):
    start_info = State()
    select_month = State()
    select_sports_item = State()
    wait_photo = State()
    
class TrainerStates(StatesGroup):
    trainer_menu = State()
    select_month = State()
    select_child = State()
    child_card = State()
    select_sports_item = State()
    history_progress = State()
    add_comment = State()

    select_sport_item_for_add_report = State()
    add_report = State()