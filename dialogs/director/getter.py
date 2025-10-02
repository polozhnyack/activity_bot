from aiogram_dialog import DialogManager
from models.methods import *
from logger import logger



async def get_count_in_review(dialog_manager: DialogManager, **kwargs):

    service: ReportService = dialog_manager.middleware_data["ReportService"]

    count = await service.get_reports_in_review_count()

    return {
        "count_in_review": count
    }


async def get_report_card(dialog_manager: DialogManager, **kwargs):
    ...