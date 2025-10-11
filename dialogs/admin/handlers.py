from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType, FSInputFile

from aiogram_dialog.widgets.kbd import Select

from dialogs.states import *
from aiogram_dialog.widgets.input import MessageInput

from models.methods import UserService, ChildService, ReportService
from models.models import *
from config import load_config
from logger import logger

import json




async def creator_child(callback: CallbackQuery, button, dialog_manager: DialogManager):
    params = callback.data.split("_")
    param = params[0]
    
    logger.debug(param)

    dialog_manager.dialog_data["param"] = param
    await dialog_manager.switch_to(state=AdminState.child_create_or_delete)


async def child_handler(
        message: Message,
        message_input: MessageInput,
        dialog_manager: DialogManager,
        **kwargs
):
    param = dialog_manager.dialog_data.get("param")
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    input_text = message.text.strip()

    if param == "create":
        parts = input_text.split(",")
        if len(parts) < 2:
            await message.answer("❌ Нужно ввести ФИ и дату рождения через запятую (например: Иван Иванов, 11.11.2011)")
            return
        full_name = parts[0].strip()
        from datetime import datetime
        try:
            birth_date = datetime.strptime(parts[1].strip(), "%d.%m.%Y").date()
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ДД.MM.ГГГГ")
            return

        child = await child_service.create(full_name=full_name, birth_date=birth_date)
        await message.answer(f"✅ Ребёнок создан: {child.full_name} ({child.code})")

    elif param == "delete":
        child_code = input_text
        success = await child_service.delete_by_code(child_code)
        if success:
            await message.answer(f"✅ Ребёнок {child_code} удалён")
        else:
            await message.answer(f"❌ Ребёнок {child_code} не найден")

    await dialog_manager.switch_to(AdminState.admin_menu)