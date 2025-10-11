from aiogram_dialog import DialogManager
from models.methods import *
from logger import logger

from utils import format_chat_username

from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType


async def get_count_in_review(dialog_manager: DialogManager, **kwargs):

    service: ReportService = dialog_manager.middleware_data["ReportService"]

    count = await service.get_reports_in_review_count()

    return {
        "count_in_review": count
    }


async def get_report_card(dialog_manager: DialogManager, **kwargs):
    report_service: ReportService = dialog_manager.middleware_data["ReportService"]
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    child_code = dialog_manager.dialog_data["child_code"]

    months = await report_service.get_months_in_review(child_code)

    selected_month = dialog_manager.dialog_data.get("selected_month")
    if not selected_month and months:
        selected_month = months[0]
        dialog_manager.dialog_data["selected_month"] = selected_month

    result = await report_service.session.execute(
        select(Report).where(
            Report.child_id == child_code,
            Report.month == selected_month,
            Report.status == ReportStatus.in_review
        )
    )
    reports = result.scalars().all()
    first_report = reports[0] if reports else None

    child: Child = await child_service.get_by_code(child_code)

    parent_username = "-"
    if child.parent_id:
        parent_chat = await dialog_manager.event.bot.get_chat(child.parent_id)
        parent_username = format_chat_username(parent_chat)

    trainer_username = "-"
    if first_report and first_report.trainer_id:
        trainer_chat = await dialog_manager.event.bot.get_chat(first_report.trainer_id)
        trainer_username = format_chat_username(trainer_chat)

    months_btn = await report_service.get_months_in_review(child_code)

    logger.debug(f"{dialog_manager.dialog_data}")

    return {
        "date": selected_month or "-",
        "full_name": child.full_name or "-",
        "birth_day": child.birth_date.strftime("%d.%m.%Y") if child.birth_date else "-",
        "child_code": child.code,
        "parent_username": parent_username,
        "trainer_username": trainer_username,
        "count_rows": len(reports),

        "months": months_btn,
    }



async def get_child_data(dialog_manager: DialogManager, **kwargs):
    service: ReportService = dialog_manager.middleware_data["ReportService"]
    child_servise: ChildService = dialog_manager.middleware_data["ChildService"]

    child_code = dialog_manager.dialog_data["child_code"]
    selected_month = dialog_manager.dialog_data["selected_month"]

    year = datetime.now().year
    month_str = f"{year}-{selected_month:02d}" 

    reports_info: list[Report] = await service.get_reports_info(
        child_code=child_code,
        month=month_str
    )
    child: Child = await child_servise.get_by_code(child_code)

    return {
        "reports_count": len(reports_info["reports"]),
        "last_report_date": reports_info["last_report_date"],
        "full_name": child.full_name,
        "birth_date": child.birth_date.strftime("%d.%m.%Y") if child.birth_date else "не указано",
        "code": child.code
    }


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