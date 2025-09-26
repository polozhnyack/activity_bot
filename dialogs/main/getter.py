from aiogram_dialog import DialogManager
from models.methods import *
from logger import logger


    
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
        "id": f"current_{current_month}",
        "name": f"🎯 {months_names[current_month-1]} (Текущий)"
    })
    
    months_sorted = sorted(months, key=lambda x: (isinstance(x["id"], str), x["id"]))
    
    return {"months": months_sorted}


async def get_child_info(dialog_manager: DialogManager, **kwargs):
    logger.debug(dialog_manager.start_data)
    
    start_data = dialog_manager.start_data or {}
    
    if start_data and not dialog_manager.dialog_data.get("child_name"):
        dialog_manager.dialog_data.update(start_data)
    
    child_birth_date = start_data.get("child_birth_date", "Не указана")
    if hasattr(child_birth_date, 'strftime'):
        formatted_date = child_birth_date.strftime("%d.%m.%Y")
    else:
        formatted_date = child_birth_date
    
    return {
        "child_name": start_data.get("child_name", "Не найдено"),
        "child_birth_date": formatted_date,
    }