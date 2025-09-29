from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType

from aiogram_dialog.widgets.kbd import Button, Select

from sqlalchemy.ext.asyncio import AsyncSession

from dialogs.states import *

from models.methods import UserService, ChildService, ReportService
from models.models import *
from config import load_config
from logger import logger


async def month_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    
    logger.debug(f"Вы выбрали месяц: {item_id}")
    await callback.answer(f"Вы выбрали месяц: {item_id}")
    dialog_manager.dialog_data["selected_month"] = int(item_id)

    logger.debug(dialog_manager.dialog_data)

    await dialog_manager.switch_to(state=TrainerStates.select_child)

async def child_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"Выбран ребенок: {item_id}")

    _, code = item_id.split("_")
    dialog_manager.dialog_data["child_code"] = code
    await dialog_manager.switch_to(state=TrainerStates.child_card)


async def get_current_history_item(dialog_manager: DialogManager, **kwargs):
    items = dialog_manager.dialog_data.get("history_items", [])
    index = dialog_manager.dialog_data.get("history_index", 0)

    if not items:
        return {"text": "Нет данных", "photo": None}  # лучше ключ "photo" для согласованности с Media widgets

    item = items[index]

    media = MediaAttachment(
        type=ContentType.PHOTO,
        file_id=MediaId(item["photo_file_id"])  # используем file_id Telegram
    )

    report: Report = item["text"]

    logger.debug(media)

    text = (
        f"Месяц - {report.month}\n"
        f"Загружено: - {report.created_at}\n"
        f"Последнее обновление - {report.updated_at}\n\n"
        f"<b>Комментарий:</b>\n\n"
        f"{report.comments or 'Нет комментариев'}"

    )

    return {
        "has_comment": bool(report.comments),
        "text": text, 
        "photo": media
        }


async def next_history(callback: CallbackQuery, button, dialog_manager: DialogManager):
    items = dialog_manager.dialog_data.get("history_items", [])
    if not items:
        return

    dialog_manager.dialog_data["history_index"] = min(
        dialog_manager.dialog_data["history_index"] + 1, len(items) - 1
    )
    await dialog_manager.switch_to(state=TrainerStates.history_progress)


async def prev_history(callback: CallbackQuery, button, dialog_manager: DialogManager):
    items = dialog_manager.dialog_data.get("history_items", [])
    if not items:
        return

    dialog_manager.dialog_data["history_index"] = max(
        dialog_manager.dialog_data["history_index"] - 1, 0
    )
    await dialog_manager.switch_to(state=TrainerStates.history_progress)


async def on_exercise_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,  
):
    exercise_id = int(item_id)
    dialog_manager.dialog_data["selected_exercise"] = exercise_id

    report_service: ReportService = dialog_manager.middleware_data["ReportService"]

    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")

    year = datetime.now().year
    month_str = f"{year}-{selected_month:02d}" 

    reports: list[Report] = await report_service.get_reports_by_child_and_month(
        child_id=child_code,
        month=month_str,
        exercise_id=exercise_id,
    )

    # reports.sort(key=lambda r: r.created_at)
    logger.debug(reports)

    history_items = []
    for report in reports:
        for photo in report.photos:
            history_items.append({
                "photo_file_id": photo.file_id,
                # "text": f"Месяц: — {report.month}\n\nКомментарий: {report.comments if report.comments else "Нет комментариев"}"
                "text": report
            })

    logger.debug(history_items)

    dialog_manager.dialog_data["history_items"] = history_items
    dialog_manager.dialog_data["history_index"] = 0

    await dialog_manager.switch_to(state=TrainerStates.history_progress)
