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
from utils import resolve_file_paths_aiogram

import json


config = load_config()

async def on_month_selected(c, widget, manager: DialogManager, item_id: str):
    logger.debug(f"Вы выбрали месяц: {item_id}")
    manager.dialog_data["selected_month"] = item_id
    await manager.switch_to(DirectorState.report) 


async def child_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"Выбран ребенок: {item_id}")

    _, code = item_id.split("_")
    dialog_manager.dialog_data["child_code"] = code
    await dialog_manager.switch_to(state=DirectorState.report)


async def child_selected_card(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    logger.debug(f"Выбран ребенок: {item_id}")

    _, code = item_id.split("_")
    dialog_manager.dialog_data["child_code"] = code
    await dialog_manager.switch_to(state=DirectorState.child_card)


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



async def on_exercise_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,  
):
    exercise_id = int(item_id)
    dialog_manager.dialog_data["selected_exercise"] = exercise_id
    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")

    year = datetime.now().year
    month_str = selected_month

    if widget.widget_id == "exercise_select":
        report_service: ReportService = dialog_manager.middleware_data["ReportService"]

        reports: list[Report] = await report_service.get_reports_by_child_and_month(
            child_id=child_code,
            month=month_str,
            exercise_id=exercise_id,
            status=ReportStatus.in_review
        )

        reports.sort(key=lambda r: r.created_at)
        logger.debug(reports)

        history_items = []
        for report in reports:
            for photo in report.photos:
                history_items.append({
                    "photo_file_id": photo.file_id,
                    "text": report
                })

        logger.debug(history_items)

        dialog_manager.dialog_data["history_items"] = history_items
        dialog_manager.dialog_data["history_index"] = 0

        await dialog_manager.switch_to(state=DirectorState.history_progress)



async def next_history(callback: CallbackQuery, button, dialog_manager: DialogManager):
    items = dialog_manager.dialog_data.get("history_items", [])
    if not items:
        return

    dialog_manager.dialog_data["history_index"] = min(
        dialog_manager.dialog_data["history_index"] + 1, len(items) - 1
    )
    await dialog_manager.switch_to(state=DirectorState.history_progress)


async def prev_history(callback: CallbackQuery, button, dialog_manager: DialogManager):
    items = dialog_manager.dialog_data.get("history_items", [])
    if not items:
        return

    dialog_manager.dialog_data["history_index"] = max(
        dialog_manager.dialog_data["history_index"] - 1, 0
    )
    await dialog_manager.switch_to(state=DirectorState.history_progress)



async def approve_report(callback: CallbackQuery, button, dialog_manager: DialogManager):
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]
    report_service: ReportService = dialog_manager.middleware_data["ReportService"]

    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")

    months_names = [
        "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август", 
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    logger.debug(f"Подтверждение отчета для ребенка {child_code} за месяц {selected_month}")

    grouped = await report_service.get_child_reports_json(child_code)

    logger.debug(json.dumps(grouped, indent=4, ensure_ascii=False))
    if selected_month not in grouped:
        await dialog_manager.event.answer("Нет данных для утверждения.", show_alert=True)
        return
    
    file_paths = await resolve_file_paths_aiogram(
        child_code=child_code,
        bot=dialog_manager.event.bot,
        reports_data=grouped,
        download_dir="temp"
    )

    logger.debug(json.dumps(file_paths, indent=4, ensure_ascii=False))
