from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group, PrevPage, NextPage, ScrollingGroup
from aiogram_dialog.widgets.media import StaticMedia, MediaScroll, DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import DirectorState
from .handlers import *
from .getter import *
from config import load_config
from dialogs.trainer.getter import get_childs_btn, months_getter, get_childs_in_review_btn

config = load_config()

products_scroller = ScrollingGroup(
    Select(
        Format("{item.full_name}"),
        id="child",
        item_id_getter=lambda p: f"code_{p.code}",
        items="childs",
        on_click=child_selected
    ),
    id="products_scroller",
    width=1,
    height=10,
    hide_on_single_page=True,
    hide_pager=True,
)


products_scroller = ScrollingGroup(
    Select(
        Format("{item.full_name}"),
        id="child",
        item_id_getter=lambda p: f"code_{p.code}",
        items="childs",
        on_click=child_selected
    ),
    id="products_scroller",
    width=1,
    height=10,
    hide_on_single_page=True,
    hide_pager=True,
)

director_dialog = Dialog(
    Window(
        Const(
            "<b>👨‍💼 Роль: Спортивный директор</b>\n\n"
            "Вы можете:\n"
            "• просматривать все отчёты на проверке;\n"
            "• видеть текущие данные и прогресс ребёнка;\n"
            "• редактировать комментарии и управлять фото;\n"
            "• утверждать отчёты (формируется PDF и отправляется родителю);\n"
            "• отклонять отчёты, отправляя их тренеру на доработку."
        ),
        Button(
            text=Const("📊 Текущие данные"), 
            id="start", 
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.select_child)
        ),
        Button(
            text=Format("📝 Ждут проверки: {count_in_review}"),
            id="In_review",
            when=lambda data, *args: int(data.get("count_in_review", 0)) > 0,
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.reports_child)
        ),
        state=DirectorState.director_menu,
        getter=get_count_in_review
    ),
    Window(
        Const("👶📊 Выберите ребёнка для проверки отчёта"),
        products_scroller,
        Row(
            PrevPage(scroll=products_scroller, text=Format("◀️")),
            NextPage(scroll=products_scroller, text=Format("▶️"))
        ),
        state=DirectorState.reports_child,
        getter=get_childs_in_review_btn
    ),
    Window(
        Format(
            "📑 <b>Отчёт за {date}</b>\n\n"

            "👶 <b>ФИО:</b> {full_name}\n"
            "🎂 <b>Дата рождения:</b> {birth_day}\n"
            "🆔 <b>Код ребёнка:</b> {child_code}\n\n"

            "🏋️ <b>Тренер:</b> @{trainer_username}\n"
            "👨‍👩‍👧 <b>Родитель:</b> @{parent_username}\n\n"

            "📷 <b>Всего записей:</b> {count_rows}"
        ),
        Button(
            text=Const("🔍 Смотреть отчёт"),
            id="check_report"
        ),
        Row(
            Button(
                text=Const("✅ Утвердить"),
                id="approve"
            ),
            Button(
                text=Const("❌ Отклонить"),
                id="reject"
            ),
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back"
        ),
        state=DirectorState.report,
        getter=get_report_card
    ),




    Window(
        Const("👶 Выберите ребёнка:"),
        products_scroller,
        Row(
            PrevPage(scroll=products_scroller, text=Format("◀️")),
            NextPage(scroll=products_scroller, text=Format("▶️"))
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.back()
        ),
        state=DirectorState.select_child,
        getter=get_childs_btn
    ),
    Window(
        Const("📅 Выберите месяц:"),
        Group(
            Select(
                Format("{item[name]}"),
                id="month_select",
                items="months",
                item_id_getter=lambda x: x["id"],
                on_click=month_selected
            ),
            width=3
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.back()
        ),
        state=DirectorState.select_month,
        getter=months_getter
    ),
    # Window(
    #     Format(
    #         "👶 Карточка ребёнка\n\n"

    #         "👤 ФИО: {full_name}\n"
    #         "📅 Дата рождения: {birth_date}\n"
    #         "🆔 Код: {code}\n\n"

    #         # "👨‍👩‍👧 Родитель: {parent_name}\n\n"

    #         "📝 Записей за месяц: {reports_count}\n"
    #         "📌 Последняя запись: {last_report_date}"
    #     ),
    #     Button(
    #         text=Const("➕ Добавить запись"),
    #         id="trainer_add_report",
    #         on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_sport_item_for_add_report)
    #     ),
    #     Button(
    #         text=Const("📈 История прогресса"),
    #         id="progres_history",
    #         on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_sports_item)
    #     ),
    #     Button(
    #         text=Const("⬅️ Назад"),
    #         id="back_menu",
    #         on_click=lambda c, b, m: m.back()
    #     ),
    #     state=TrainerStates.child_card,
    #     # getter=get_child_data
    # ),
)