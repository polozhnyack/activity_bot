from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group, PrevPage, NextPage, ScrollingGroup
from aiogram_dialog.widgets.media import StaticMedia, MediaScroll, DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import TrainerStates
from .handlers import *
from .getter import *
from config import load_config

config = load_config()

products_scroller = ScrollingGroup(
    Select(
        Format("{item[full_name]} · {item[progress]}% {item[progress_emoji]}"),
        id="child",
        item_id_getter=lambda p: f"code_{p['code']}",
        items="childs",
        on_click=child_selected
    ),
    id="products_scroller",
    width=2,
    height=20,
    hide_on_single_page=True,
    hide_pager=True,
)


child_history_scroller = ScrollingGroup(
    Select(
        Format("{item.full_name}"),
        id="child",
        item_id_getter=lambda p: f"code_{p.code}",
        items="childs",
        on_click=child_selected_history
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
        Const(
            '\nЧто бы вернуться в режим администратора, нажмите /start или кнопку "Назад в админ меню".',
            when="admin"
            ),
        Button(
            text=Const("➡️ Начать работу"), 
            id="start", 
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_month)
        ),
        Button(
            text=Const("📜 Смотреть историю"),
            id="history",
            on_click=lambda c, b, m: m.start(state=ProgressHistory.history_menu)
        ),
        Button(
            text=Const("⬅️ Назад в админ меню"),
            id="back_to_admin",
            on_click=lambda c, b, m: m.start(state=AdminState.admin_menu),
            when="admin"
        ),
        state=TrainerStates.trainer_menu,
        getter=get_trainer_menu_data
    ),
    Window(
        Format("📅 <b>Выберите месяц · {year}</b>"),
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
            on_click=back_to
        ),
        state=TrainerStates.select_month,
        getter=months_getter
    ),
    Window(
        Format(
            "👶 Выберите ребёнка:\n\n"
            "Прогресс за <b>месяц {month_view}</b>:\n"
            "⚪️ 0% · 🔴 до 40% · 🟡 40–69% · 🟢 70%+"
        ),
        Const(
            "\n📄 На одной странице отображается до 20 детей. Используйте ◀️ ▶️ для навигации",
            when=lambda data, *args: data.get("show_pager", False)
        ),
        products_scroller,
        Row(
            PrevPage(
                scroll=products_scroller,
                text=Format("◀️"),
                # when=lambda data, *args: logger.debug(f"PrevPage when data: {data}") or True
            ),
            NextPage(
                scroll=products_scroller,
                text=Format("▶️"),
                # when=lambda data, *args: logger.debug(f"NextPage when data: {data}") or True
            ),

            when=lambda data, *args: data.get("show_pager", False)
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

            "📅 Месяц: <b>{month_view}</b>\n"
            "📊 <b>Заполнено: {month_progress_percent}%</b>\n\n"

            "👤 ФИО: {full_name}\n"
            "📅 Дата рождения: {birth_date}\n"
            "🆔 Код: {code}\n"
            "🏆 <b>Уровень:</b> {level}\n\n"

            "📝 Записей за месяц: {reports_count}\n"
            "📌 Последняя запись: {last_report_date}\n\n"

            "📅 ОФП:\n{month_plan}"
        ),
        Select(
            text=Format("{item[name]}"),
            items="child_scroller_items",
            item_id_getter=lambda x: f"{x['code']}",
            id="child_scroller",
            on_click=child_scroll_on_page,
            when=lambda data, *args: bool(data.get("child_scroller_items"))
        ),
        Button(
            text=Const("➕ Добавить запись"),
            id="trainer_add_report",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_sport_item_for_add_report)
        ),
        Button(
            text=Const("📊 Добавить ОФП"),
            id="add_plan_month",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.plane_input)
        ),
        Button(
            text=Const("📈 Записи"),
            id="progres_history",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_sports_item)
        ),
        Button(
            text=Const("✅ Завершить месяц"),
            id="complete_month",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.confidence_window)
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.back()
        ),
        state=TrainerStates.child_card,
        getter=get_child_data
    ),
    Window(
        Const("Выберите спортивный элемент"),
        Group(
            Select(
                Format("{item[name]}"),
                id="exercise_select",
                items="exercises",
                item_id_getter=lambda x: x["id"],
                on_click=on_exercise_selected,
            ),
            width=1
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(TrainerStates.child_card)
        ),
        state=TrainerStates.select_sports_item,
        getter=get_exercise_btn
    ),
    Window(
        Const("Выберите спортивный элемент"),
        Group(
            Select(
                Format("{item[name]}"),
                id="select_sport_item_for_add_report",
                items="exercises",
                item_id_getter=lambda x: x["id"],
                on_click=on_exercise_selected,
            ),
            width=1
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(TrainerStates.child_card)
        ),
        state=TrainerStates.select_sport_item_for_add_report,
        getter=get_exercise_btn
    ),
    Window(
        Const(
            "📸 <b>Пожалуйста, отправьте фото — с подписью или без неё</b>\n\n"
            "Вы можете добавить комментарий к фото позже, если захотите."
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(TrainerStates.select_sport_item_for_add_report)
        ),
        MessageInput(
            select_sport_item_for_add_report,
            content_types=ContentType.PHOTO
        ),
        state=TrainerStates.add_report
    ),
    Window(
        Format("{text}"),
        DynamicMedia("photo"),
        Row(
            Button(text=Const("◀️"), id="prev", on_click=prev_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
            Button(text=Const("▶️"), id="next", on_click=next_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
        ),
        Button(
            text=Const("✏️ Добавить комментарий"),
            id="add_comment",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.add_comment),
            when=lambda data, widget, manager: data.get("text") != "Нет данных" and not data.get("has_comment")
        ),
        Button(
            text=Const("📝 Изменить комментарий"),
            id="edit_comment",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.add_comment),
            when=lambda data, widget, manager: data.get("text") != "Нет данных" and data.get("has_comment"),
        ),
        Button(
            text=Const("🗑️ Удалить запись"),
            id="delete_report",
            on_click=on_delete_report,
            when=lambda data, widget, manager: data.get("text") != "Нет данных"
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(state=TrainerStates.select_sports_item)
        ),
        state=TrainerStates.history_progress,
        getter=get_current_history_item
    ),
    Window(
        DynamicMedia("photo", when="has_photo"),
        Const(
            "✍️ Отправьте текст комментария.\n\n"
            "➡️ Просто напишите сообщение ниже, и оно сохранится к отчёту."
          ),
        MessageInput(
            on_add_comment,
            content_types=ContentType.TEXT
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(TrainerStates.history_progress)
        ),
        state=TrainerStates.add_comment,
        getter=get_photo_to_comment
    ),
    Window(
        Const("⚠️ <b>Подтверждение действия</b>\n\n"
          "Вы уверены, что хотите <b>закрыть месяц</b> "
          "и 📤 отправить отчет на проверку?\n\n"
        ),
        Row(
            Button(
                Const("✅ Да"),
                id="confirm_yes",
                on_click=on_confirm_close
            ),
            Button(
                Const("❌ Нет"),
                id="confirm_no",
                on_click=lambda c, b, m: m.switch_to(state=TrainerStates.child_card)
                ),
        ),
        state=TrainerStates.confidence_window
    ),
    Window(
        Const(
            "📝 Введите план на месяц"
        ),
        MessageInput(
            plane_input_handler,
            content_types=ContentType.TEXT
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(TrainerStates.child_card)
        ),
        state=TrainerStates.plane_input
    )
)


progress_history = Dialog(
    Window(
        Const("👶 Выберите ребенка для просмотра истории прогресса."),
        child_history_scroller,
        Row(
            PrevPage(scroll=child_history_scroller, text=Format("◀️")),
            NextPage(scroll=child_history_scroller, text=Format("▶️")),
            when=lambda data, *args: data.get("show_pager", False)
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=exit_from_history
        ),
        state=ProgressHistory.history_menu,
        getter=get_childs_btn
    ),
    Window(
        Const("📅 Выберите месяц, за который хотите посмотреть историю."),
        Group(
            Select(
                Format("{item[name]}"),
                id="month_select",
                items="months",
                item_id_getter=lambda x: x["id"],
                on_click=history_month_selected
            ),
            width=3
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(ProgressHistory.history_menu)
        ),
        getter=months_getter,
        state=ProgressHistory.select_month
    ),
    Window(
        Format("{text}"),
        DynamicMedia("photo"),
        Row(
            Button(text=Const("◀️"), id="prev", on_click=prev_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
            Button(text=Const("▶️"), id="next", on_click=next_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(state=ProgressHistory.select_month)
        ),
        state=ProgressHistory.child_history,
        getter=get_current_history_item
    )
)