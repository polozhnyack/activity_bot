from aiogram_dialog import DialogManager
from models.methods import *
from models.models import ROLE_NAMES
from logger import logger

from utils import format_chat_username

from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType


async def get_count_in_review(dialog_manager: DialogManager, **kwargs):

    service: ReportService = dialog_manager.middleware_data["ReportService"]
    user_service: UserService = dialog_manager.middleware_data["UserService"]

    user = await user_service.get_by_id(dialog_manager.event.from_user.id)
    if user.role not in (UserRole.director_novice, UserRole.director_pro):
        return
    
    count = await service.get_reports_in_review_count(int(dialog_manager.event.from_user.id))


    return {
        "count_in_review": count,
        "director_role": ROLE_NAMES.get(user.role)
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


    plans: MonthlyPlan = await child_service.get_monthly_plan(
        child_id=child_code,
        month=selected_month
    )

    if not plans:
        month_plan = "Планов на этот месяц не найдено"
    else:
        month_plan = plans[0].notes if plans[0].notes else "План пустой"

    months_with_markers = []
    for m in months_btn:
        if m == selected_month:
            months_with_markers.append(f"● {m} ●")
        else:
            months_with_markers.append(m)



    return {
        "date": selected_month or "-",
        "full_name": child.full_name or "-",
        "birth_day": child.birth_date.strftime("%d.%m.%Y") if child.birth_date else "-",
        "child_code": child.code,
        "parent_username": parent_username,
        "trainer_username": trainer_username,
        "count_rows": len(reports),
        "level": child.level.name,
        "months": months_with_markers,

        "month_plan": month_plan
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


# async def get_current_history_item(dialog_manager: DialogManager, **kwargs):
#     items = dialog_manager.dialog_data.get("history_items", [])
#     index = dialog_manager.dialog_data.get("history_index", 0)

#     ex_service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]

#     if not items:
#         return {"text": "Нет данных", "photo": None}

#     item = items[index]


#     photo_file_id = item.get("photo_file_id")
#     if photo_file_id:
#         media = MediaAttachment(
#             type=ContentType.PHOTO,
#             file_id=MediaId(photo_file_id)
#         )
#     else:
#         media = None  # нет фото

#     report: Report = item["text"]

#     month_plan: str = item.get("month_plan", "План не найден")

#     dialog_manager.dialog_data["selected_report"] = int(report.id)

#     exercise_name = "-"
#     if report.photos and report.photos[0].exercise_id:
#         exercise_name = await ex_service.get_exercise_name_by_id(report.photos[0].exercise_id)

#     text = (
#         f"📅 <b>Отчёт за:</b> {report.month}\n"
#         f"🏋️‍♂️ <b>Упражнение:</b> {exercise_name or 'Не указано'}\n\n"
#         f"💬 <b>Комментарий тренера:</b>\n"
#         f"{report.comments[-1].text if report.comments else 'Нет комментариев'}"
#     )

#     logger.debug(text)

#     return {
#         "has_comment": bool(report.comments),
#         "text": text, 
#         "photo": media,
#         }


async def get_current_history_item(dialog_manager: DialogManager, **kwargs):
    ex_service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]
    report_service: ReportService = dialog_manager.middleware_data["ReportService"]
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")
    exercise_id = dialog_manager.dialog_data.get("selected_exercise")

    if not (child_code and selected_month and exercise_id):
        return {"text": "Нет данных", "photo": None}

    reports: list[Report] = await report_service.get_reports_by_child_and_month(
        child_id=child_code,
        month=selected_month,
        exercise_id=exercise_id,
        status=ReportStatus.in_review
    )

    if not reports:
        return {"text": "Нет отчётов", "photo": None}

    report = sorted(reports, key=lambda r: r.created_at)[-1]

    plans: MonthlyPlan = await child_service.get_monthly_plan(
        child_id=child_code,
        month=selected_month
    )

    month_plan = "-"
    if plans and plans[0].notes:
        month_plan = plans[0].notes

    photo_file_id = report.photos[0].file_id if report.photos else None

    if photo_file_id:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(photo_file_id)
        )
    else:
        media = None


    dialog_manager.dialog_data["current_photo"] = media

    exercise_name = "-"
    if report.photos and report.photos[0].exercise_id:
        exercise_name = await ex_service.get_exercise_name_by_id(report.photos[0].exercise_id)

    text = (
        f"📅 <b>Отчёт за:</b> {report.month}\n"
        f"🏋️‍♂️ <b>Упражнение:</b> {exercise_name or 'Не указано'}\n\n"
        f"💬 <b>Комментарий тренера:</b>\n"
        f"{report.comments[-1].text if report.comments else 'Нет комментариев'}"
    )

    dialog_manager.dialog_data["selected_report"] = int(report.id)

    return {
        "has_comment": bool(report.comments),
        "text": text,
        "photo": media,
    }



async def get_photo_to_comment(dialog_manager: DialogManager, **kwargs):

    media: MediaAttachment = dialog_manager.dialog_data.get("current_photo")

    return {
        "has_photo": bool(media),
        "photo": media
        }
