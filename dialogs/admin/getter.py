from aiogram_dialog import DialogManager
from models.methods import *
from logger import logger


async def child_create_delete_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    param = dialog_manager.dialog_data.get("param")
    if param == "create":
        text = "Введите ФИ и дату рождения через запятую (например: Иван Иванов, 11.11.2011)"
    else:
        text = "Введите код ребёнка для удаления"
    return {"child_create_or_delete_text": text}



async def get_roles_data(dialog_manager: DialogManager, **kwargs):
    role_names = {
        "parent": "👨‍👩‍👧 Родитель",
        "trainer": "💪 Тренер",
        "director": "🎓 Директор",
        "admin": "🛠 Администратор",
    }

    return {
        "role_editor_text": "Выберите роль, которую хотите назначить 👇",
        "roles": [
            (role_names[role.value], role.value)
            for role in UserRole
            if role.value != "admin"
        ],
    }

