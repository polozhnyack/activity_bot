from aiogram_dialog import DialogManager
from models.methods import *
from logger import logger
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.enums import ContentType


async def months_getter(dialog_manager, **kwargs):
    from datetime import datetime
    
    months_names = [
        "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август", 
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    months = [
        {"id": month_number, "name": f"{months_names[month_number-1]}"}
        for month_number in range(1, 13)
    ]
    
    months.append({
        "id": f"{current_month}",
        "name": f"🎯 {months_names[current_month-1]} (Текущий)"
    })
    
    months_sorted = sorted(months, key=lambda x: (isinstance(x["id"], str), x["id"]))
    
    return {"months": months_sorted}


async def get_childs_btn(dialog_manager: DialogManager, **kwargs):
    service: ChildService = dialog_manager.middleware_data["ChildService"]
    childs: list[Child] = await service.get_all()
    childs = [c for c in childs if c.full_name]

    page_size = 10
    total_pages = (len(childs) - 1) // page_size + 1

    show_pager = total_pages > 1

    return {
        "show_pager": show_pager,
        "childs": childs,
        "current_page": 0,
        "total_pages": total_pages
    }


async def get_childs_in_review_btn(dialog_manager: DialogManager, **kwargs):
    service: ChildService = dialog_manager.middleware_data["ChildService"]

    childs: list[Child] = await service.get_children_with_reports_in_review()
    childs = [c for c in childs if c.full_name]

    return {
        "childs": childs
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

    plans: MonthlyPlan = await child_servise.get_monthly_plan(
        child_id=child_code,
        month=month_str
    )

    if not plans:
        month_plan = "-"
    else:
        month_plan = plans[0].notes if plans[0].notes else "-"

    return {
        "reports_count": len(reports_info["reports"]),
        "last_report_date": reports_info["last_report_date"],
        "full_name": child.full_name,
        "level": child.level.name,
        "birth_date": child.birth_date.strftime("%d.%m.%Y") if child.birth_date else "не указано",
        "code": child.code,
        "month_plan": month_plan
    }


async def get_exercise_btn(dialog_manager: DialogManager, **kwargs):
    service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]

    child_code = dialog_manager.dialog_data["child_code"]

    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    child: Child = await child_service.get_by_code(child_code)

    if not child.level_id:
        return {"exercises": []} 

    # exercises = await service.get_by_level(child.level_id)

    month = int(dialog_manager.dialog_data["selected_month"])

    year = datetime.now().year
    month_str = f"{year}-{month:02d}" 

    logger.debug(f"Getting exercises stats for child {child.code} for month {month_str}")

    ex = await service.get_exercises_stats_by_child_month(
        child_id=child.code,
        month=month_str,
        level_id=child.level_id
    )

    logger.debug(f"Exercises stats: {ex}")

    def format_counter(count: int, emoji: str) -> str:
        if count <= 0:
            return ""
        return f"{emoji} x{count}"

    return {
        "exercises": [
            {
                "id": item["exercise"].id,
                "name": (
                    f"{item['exercise'].name} "
                    f"{format_counter(item['photos_count'], '📸')} "
                    f"{format_counter(item['comments_count'], '💬')}"
                ).strip(),
            }
            for item in ex
        ]
    }



async def get_exercise_text(dialog_manager: DialogManager, **kwargs):
    service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]

    exercises_name = await service.get_exercise_name_by_id(dialog_manager.dialog_data["selected_exercise"])

    return {
        "element_name": exercises_name
    }


async def get_trainer_menu_data(dialog_manager: DialogManager, **kwargs):

    user_service: UserService = dialog_manager.middleware_data["UserService"]
    if not user_service:
        return {"admin": False}
    user = await user_service.get_by_id(dialog_manager.event.from_user.id)

    is_admin = user and user.role == UserRole.admin

    return {"admin": is_admin}