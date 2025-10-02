from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType

from aiogram_dialog.widgets.kbd import Select

from dialogs.states import *
from aiogram_dialog.widgets.input import MessageInput

from models.methods import UserService, ChildService, ReportService
from models.models import *
from config import load_config
from logger import logger
from dialogs.trainer.getter import get_childs_btn



async def child_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"Выбран ребенок: {item_id}")

    _, code = item_id.split("_")
    dialog_manager.dialog_data["child_code"] = code
    await dialog_manager.switch_to(state=DirectorState.select_month)

async def report_child_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"Выбран ребенок: {item_id}")

    _, code = item_id.split("_")
    dialog_manager.dialog_data["child_code"] = code
    await dialog_manager.switch_to(state=DirectorState.report)

async def month_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"ID кнопки: {widget.widget_id}")
    logger.debug(f"Вы выбрали месяц: {item_id}")
    await callback.answer(f"Вы выбрали месяц: {item_id}")
    dialog_manager.dialog_data["selected_month"] = int(item_id)

    logger.debug(dialog_manager.dialog_data)

    await dialog_manager.switch_to(state=DirectorState.select_child)