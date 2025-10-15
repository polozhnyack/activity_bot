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

    confidence_window = State()

    plane_input = State()


class DirectorState(StatesGroup):
    director_menu = State()
    select_child = State()
    select_month = State()

    reports_child = State()
    report = State()
    report_list = State()

    select_elements_in_review = State()
    report_review = State()
    history_progress = State()

    agree_to_approve_report = State()
    reject_report = State()
    

class AdminState(StatesGroup):
    admin_menu = State()

    child_create_or_delete = State()
    grant_or_revoke_role = State()

    role_select = State()
    user_select = State()


class ProgressHistory(StatesGroup):
    history_menu = State()
    select_month = State()
    child_history = State()