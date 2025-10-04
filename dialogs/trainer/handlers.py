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



async def back_to(
    callback: CallbackQuery,
    button,
    dialog_manager: DialogManager
):
    service: UserService = dialog_manager.middleware_data["UserService"]
    user: User = await service.get_by_id(callback.from_user.id)


    if user and user.role == UserRole.director:
        await dialog_manager.start(state=DirectorState.director_menu)
    else:
        await dialog_manager.back()

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
        return {"text": "Нет данных", "photo": None}

    item = items[index]

    media = MediaAttachment(
        type=ContentType.PHOTO,
        file_id=MediaId(item["photo_file_id"])
    )

    report: Report = item["text"]

    dialog_manager.dialog_data["selected_report"] = int(report.id)

    text = (
        f"Месяц - {report.month}\n"
        f"Загружено: - {report.created_at}\n"
        f"Последнее обновление - {report.updated_at}\n\n"
        f"<b>Комментарий:</b>\n\n"
        f"{report.comments[-1].text if report.comments else "Нет комментариев"}"
    )

    logger.debug(text)

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
    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")

    year = datetime.now().year
    month_str = f"{year}-{selected_month:02d}" 

    if widget.widget_id == "exercise_select":
        report_service: ReportService = dialog_manager.middleware_data["ReportService"]

        reports: list[Report] = await report_service.get_reports_by_child_and_month(
            child_id=child_code,
            month=month_str,
            exercise_id=exercise_id,
            status=ReportStatus.draft
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

        await dialog_manager.switch_to(state=TrainerStates.history_progress)

    elif widget.widget_id == "select_sport_item_for_add_report":
        await dialog_manager.switch_to(state=TrainerStates.add_report)





async def on_add_comment(message: Message, _: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправьте только текст")
        return
    
    report_id: Report = manager.dialog_data.get("selected_report")
    if not report_id:
        await message.answer("❌ Ошибка: отчет не выбран")
        return

    report_service: ReportService = manager.middleware_data["ReportService"]

    await report_service.add_comment(
        report_id=report_id,
        author_id=message.from_user.id,
        text=message.text.strip(),
    )

    child_code = manager.dialog_data.get("child_code")
    selected_month = manager.dialog_data.get("selected_month")
    exercise_id = manager.dialog_data["selected_exercise"]

    year = datetime.now().year
    month_str = f"{year}-{selected_month:02d}" 


    reports: list[Report] = await report_service.get_reports_by_child_and_month(
        child_id=child_code,
        month=month_str,
        exercise_id=exercise_id,
        status=ReportStatus.draft
    )

    reports.sort(key=lambda r: r.created_at)

    new_history_items = []
    for report in reports:
        for photo in report.photos:
            new_history_items.append({
                "photo_file_id": photo.file_id,
                "text": report
            })

    old_history_items = manager.dialog_data.get("history_items", [])

    if old_history_items != new_history_items:
        logger.debug("history_items обновлен!")
        manager.dialog_data["history_items"] = new_history_items

    manager.dialog_data["history_index"] = manager.dialog_data["history_index"]

    if new_history_items:
        current_item = new_history_items[manager.dialog_data["history_index"]]
        report: Report = current_item["text"]
        logger.debug(
            f"Текущий report после обновления: "
            f"ID={report.id}, "
            f"comments={[c.text for c in report.comments]}, "
            f"updated_at={report.updated_at}"
        )

    await message.answer("✅ Комментарий добавлен")
    await manager.switch_to(state=TrainerStates.history_progress)



async def on_delete_report(event, widget, dialog_manager: DialogManager, **kwargs):
    report_service: ReportService = dialog_manager.middleware_data["ReportService"]

    selected_month = dialog_manager.dialog_data.get("selected_month")
    year = datetime.now().year
    month_str = f"{year}-{selected_month:02d}" 

    await report_service.delete_report(
        child_id=dialog_manager.dialog_data.get("child_code"),
        month=month_str,
        report_id=dialog_manager.dialog_data.get("selected_report")
    )

    child_code = dialog_manager.dialog_data.get("child_code")
    exercise_id = dialog_manager.dialog_data.get("selected_exercise")
    
    reports: list[Report] = await report_service.get_reports_by_child_and_month(
        child_id=child_code,
        month=month_str,
        exercise_id=exercise_id,
        status=ReportStatus.draft
    )

    new_history_items = [
        {"photo_file_id": photo.file_id, "text": report}
        for report in reports
        for photo in report.photos
    ]
    
    dialog_manager.dialog_data["history_items"] = new_history_items
    dialog_manager.dialog_data["history_index"] = 0

    await dialog_manager.update(data=dialog_manager.dialog_data)


async def select_sport_item_for_add_report(
    message: Message,
    _: MessageInput,
    manager: DialogManager
):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте именно фото.")
        return

    report_service: ReportService = manager.middleware_data["ReportService"]

    photo = message.photo[-1]
    file_id = photo.file_id
    caption = message.caption or None
    selected_month = manager.dialog_data.get("selected_month")


    logger.debug(f"Получено фото: {file_id}, подпись: {caption}")

    await report_service.create_report_photo(
        user_id=message.from_user.id,
        child_code=manager.dialog_data.get("child_code"),
        photo_file_id=file_id,
        exercise_id=manager.dialog_data["selected_exercise"],
        trainer_id=message.from_user.id,
        month=selected_month,
        comment_text=caption
    )

    await message.answer("✅ Отчет добавлен.")
    await manager.switch_to(state=TrainerStates.child_card)


async def on_confirm_close(callback: CallbackQuery, button, dialog_manager: DialogManager):
    
    child_id = dialog_manager.dialog_data["child_code"]
    month = dialog_manager.dialog_data["selected_month"]
    trainer_id = callback.from_user.id

    service: ReportService = dialog_manager.middleware_data["ReportService"]

    year = datetime.now().year
    month_str = f"{year}-{month:02d}" 

    if await service.send_reports_to_review(
        child_id=child_id,
        trainer_id=trainer_id,
        month=month_str
    ):
        await callback.answer("✅ Отчёты закрыты и отправлены на проверку.", show_alert=True)
    else:
        await callback.answer("❌ Отчетов за месяц не найдено.", show_alert=True)

    await dialog_manager.switch_to(state=TrainerStates.select_month)