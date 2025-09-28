from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group, PrevPage, NextPage, ScrollingGroup
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import TrainerStates
from .handlers import *
from .getter import *
from config import load_config

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

trainer_dialog = Dialog(
    Window(
        Const(
            "<b>👨‍🏫 Роль: Тренер</b>\n\n"
            "Вы можете:\n"
            "• выбрать ребёнка и месяц;\n"
            "• просматривать фото и комментарии за текущий месяц;\n"
            "• видеть историю предыдущих месяцев;\n"
            "• добавлять комментарии и план;\n"
            "• завершать месяц (отчёт отправляется директору)."
        ),
        Button(
            text=Const("➡️ Начать работу"), 
            id="start", 
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_month)
        ),
        state=TrainerStates.trainer_menu,
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
        state=TrainerStates.select_month,
        getter=months_getter
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
        state=TrainerStates.select_child,
        getter=get_childs_btn
    ),
    Window(
        Format(
            "👶 Карточка ребёнка\n\n"

            "👤 ФИО: {full_name}\n"
            "📅 Дата рождения: {birth_date}\n"
            "🆔 Код: {code}\n\n"

            # "👨‍👩‍👧 Родитель: {parent_name}\n\n"

            "📝 Записей за месяц: {reports_count}\n"
            "📌 Последняя запись: {last_report_date}"
        ),
        Button(
            text=Const("📈 История прогресса"),
            id="progres_history"
            
        ),
        Button(
            text=Const("✅ Завершить месяц"),
            id="complete_month"
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.back()
        ),
        state=TrainerStates.child_card,
        getter=get_child_data
    )
)