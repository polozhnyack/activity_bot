from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities.media import MediaAttachment, MediaId
from aiogram.types import ContentType, FSInputFile

from aiogram_dialog.widgets.kbd import Select

from dialogs.states import *
from aiogram_dialog.widgets.input import MessageInput

from models.methods import UserService, ChildService, ReportService
from models.models import *
from config import load_config
from logger import logger
from dialogs.trainer.getter import get_childs_btn
from utils import resolve_file_paths_aiogram, generate_progress_html_vertical, render_html_to_pdf, html_code_creator, remove_files

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
        child_service: ChildService = dialog_manager.middleware_data["ChildService"]

        reports: list[Report] = await report_service.get_reports_by_child_and_month(
            child_id=child_code,
            month=month_str,
            exercise_id=exercise_id,
            status=ReportStatus.in_review
        )

        plans: MonthlyPlan = await child_service.get_monthly_plan(
            child_id=child_code,
            month=month_str
        )

        if not plans:
            month_plan = "Планов на этот месяц не найдено"
        else:
            month_plan = plans[0].notes if plans[0].notes else "План пустой"


        reports.sort(key=lambda r: r.created_at)
        logger.debug(reports)

        history_items = []
        for report in reports:
            for photo in report.photos:
                history_items.append({
                    "photo_file_id": photo.file_id,
                    "text": report,
                    "month_plan": month_plan
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

    logger.debug(f"Подтверждение отчета для ребенка {child_code} за месяц {selected_month}")

    grouped = await report_service.get_child_reports_json(child_code)

    child: Child = await child_service.get_by_code(child_code)

    logger.debug(json.dumps(grouped, indent=4, ensure_ascii=False))
    if selected_month not in grouped:
        await dialog_manager.event.answer("Нет данных для утверждения.", show_alert=True)
        return
    
    report_data = await resolve_file_paths_aiogram(
        child_code=child_code,
        bot=dialog_manager.event.bot,
        child_service=dialog_manager.middleware_data["ChildService"],
        reports_data=grouped,
        download_dir="temp"
    )

    logger.debug(json.dumps(report_data, indent=4, ensure_ascii=False))
    html_table = generate_progress_html_vertical(report_data, child.full_name)

    full_html = html_code_creator(html_table)

    with open("progress_journal.html", "w", encoding="utf-8") as f:
        f.write(full_html)

    clean_name = lambda name: name.replace(" ", "_").lower()
    child_name_clean = clean_name(child.full_name)

    pdf_path = render_html_to_pdf(full_html, f"{child_name_clean}.pdf")

    try:
        await callback.bot.send_document(
            chat_id=child.parent_id,
            document=FSInputFile(path=pdf_path),
            caption=f"<b>📄 Отчёт по ученику:</b> {child.full_name}",
            parse_mode="HTML"
        )
        await callback.message.answer("✅ Отчёт успешно отправлен родителю.")
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось отправить отчёт родителю.\nОшибка: {e}")

    try:
        remove_files(report_data)
    except Exception as e:
        logger.error(f"Ошибка удаления файлов: {e}")
    
    await dialog_manager.done()



async def reject_report(callback: CallbackQuery, button, dialog_manager: DialogManager):
    child_code = dialog_manager.dialog_data.get("child_code")
    selected_month = dialog_manager.dialog_data.get("selected_month")

    report_service: ReportService = dialog_manager.middleware_data["ReportService"]
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    child: Child = await child_service.get_by_code(child_code)

    success, trainer_id = await report_service.reset_reports_to_draft(
        child_code=child_code,
        selected_month=selected_month
    )

    if not success:
        await callback.message.answer(
            "❌ Не удалось отклонить отчёт: либо отчётов нет, либо у них разные тренеры."
        )
        await callback.answer()
        return

    if trainer_id:
        try:
            await callback.bot.send_message(
                chat_id=trainer_id,
                text=(
                    f"❌ Отчёт за {selected_month} для ребёнка {child.full_name} был отклонён.\n"
                    "Отчёт вернулся в статус 'Создан'."
                )
            )
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при отправке сообщения тренеру: {e}")
            logger.error(f"Ошибка при отправке сообщения тренеру: {e}")

    await callback.message.answer("✅ Отчёт успешно отклонён.")
    await dialog_manager.switch_to(DirectorState.director_menu)