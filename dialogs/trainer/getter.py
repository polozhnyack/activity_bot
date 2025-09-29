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

    childs.sort(key=lambda c: c.full_name.lower())

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

    return {
        "reports_count": len(reports_info["reports"]),
        "last_report_date": reports_info["last_report_date"],
        "full_name": child.full_name,
        "birth_date": child.birth_date.strftime("%d.%m.%Y") if child.birth_date else "не указано",
        "code": child.code
    }


async def get_exercise_btn(dialog_manager: DialogManager, **kwargs):
    service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]

    exercises = await service.get_all()

    return {
        "exercises": [
            {"id": ex.id, "name": ex.name}
            for ex in exercises
        ]
    }


async def get_exercise_text(dialog_manager: DialogManager, **kwargs):
    service: ExerciseService = dialog_manager.middleware_data["ExerciseService"]

    exercises_name = await service.get_exercise_name_by_id(dialog_manager.dialog_data["selected_exercise"])

    return {
        "element_name": exercises_name
    }