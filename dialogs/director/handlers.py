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
from utils import resolve_file_paths_aiogram, generate_progress_html_vertical, render_html_to_pdf, html_code_creator, remove_files, delete_file

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
            month_plan = "-"
        else:
            month_plan = plans[0].notes if plans[0].notes else "-"


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

    try:
        logger.info(f"Подтверждение отчетов для ребенка {child_code} за месяц {selected_month}")
        await report_service.approve_reports_by_child_and_month(
            child_code=child_code,
            selected_month=selected_month
        )
        logger.debug("approve_reports_by_child_and_month выполнено успешно")
    except Exception as e:
        logger.critical(f"Ошибка при утверждении отчетов для child_code={child_code}, month={selected_month}")

    grouped = await report_service.get_child_reports_json(child_code)
    logger.debug(f"grouped reports: {json.dumps(grouped, indent=4, ensure_ascii=False)}")

    child: Child = await child_service.get_by_code(child_code)
    logger.debug(f"Child загружен: {child}")

    logger.debug(json.dumps(grouped, indent=4, ensure_ascii=False))
    if selected_month not in grouped:
        logger.warning(f"Нет отчетов за месяц={selected_month}, child_code={child_code}")
        await dialog_manager.event.answer("Нет данных для утверждения.", show_alert=True)
        return
    
    report_data = await resolve_file_paths_aiogram(
        child_code=child_code,
        bot=dialog_manager.event.bot,
        child_service=dialog_manager.middleware_data["ChildService"],
        reports_data=grouped,
        download_dir="temp"
    )
    logger.debug(f"report_data подготовлены: {report_data}")

    logger.debug(json.dumps(report_data, indent=4, ensure_ascii=False))
    html_table = generate_progress_html_vertical(report_data, child.full_name)

    full_html = html_code_creator(html_table)

    clean_name = lambda name: name.replace(" ", "_").lower()
    child_name_clean = clean_name(child.full_name)

    pdf_path = render_html_to_pdf(full_html, f"{child_name_clean}.pdf")
    logger.debug(f"PDF сгенерирован: {pdf_path}")

    try:
        if child.parent_id:
            try:
                await callback.bot.send_document(
                    chat_id=child.parent_id,
                    document=FSInputFile(path=pdf_path),
                    caption=f"<b>📄 Отчёт по ученику:</b> {child.full_name}",
                    parse_mode="HTML"
                )
                parent_status = "✅ Отчет родителю успешно отправлен."
                logger.debug("Отчет отправлен родителю")
            except Exception as e:
                parent_status = f"⚠️ Не удалось отправить отчет родителю: {e}"
        else:
            parent_status = "⚠️ Отчет родителю не отправлен: ребенок не привязан к родителю."

        await callback.bot.send_document(
            chat_id=callback.from_user.id,
            document=FSInputFile(path=pdf_path),
            caption=f"<b>📄 Отчёт по ученику:</b> {child.full_name}\n"
                    f"(Копия для вас)",
            parse_mode="HTML"
        )
        logger.debug("Копия отчета отправлена пользователю")
        await callback.message.answer(f"{parent_status}\n📨 Копия отчёта отправлена вам.")

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при отправке отчёта.\n{e}")

    try:
        remove_files(report_data)
        delete_file(pdf_path)
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


async def on_edit_comment(message: Message, _: MessageInput, manager: DialogManager):
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

    await message.answer("✅ Комментарий добавлен")
    await manager.switch_to(state=DirectorState.select_elements_in_review)



async def on_edit_photo(message: Message, _: MessageInput, manager: DialogManager):
    if not message.photo:
        await message.answer("⚠️ Пожалуйста, отправьте фотографию")
        return
    
    report_id: Report = manager.dialog_data.get("selected_report")
    if not report_id:
        await message.answer("❌ Ошибка: отчет не выбран")
        return

    report_service: ReportService = manager.middleware_data["ReportService"]

    photo_size = message.photo[-1]
    file_id = photo_size.file_id

    await report_service.update_photo_by_report_id(
        report_id=int(report_id),
        new_file_id=file_id
    )

    await message.answer("✅ Фото успешно обновлено")
    await manager.switch_to(state=DirectorState.select_elements_in_review)