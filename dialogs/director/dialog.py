from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group, PrevPage, NextPage, ScrollingGroup, Radio
from aiogram_dialog.widgets.media import StaticMedia, MediaScroll, DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import DirectorState
from .handlers import *
from .getter import *
from config import load_config
from dialogs.trainer.getter import get_childs_btn, months_getter, get_childs_in_review_btn, get_exercise_btn

import operator

config = load_config()

products_scroller = ScrollingGroup(
    Select(
        Format("{item.full_name}"),
        id="child",
        item_id_getter=lambda p: f"code_{p.code}",
        items="childs",
        on_click=child_selected_card
    ),
    id="products_scroller",
    width=1,
    height=10,
    hide_on_single_page=True,
    hide_pager=True,
)

months_select = Group(
    Select(
        Format("{item}"),
        id="s_months",
        item_id_getter=lambda x: x.replace("● ", "").replace(" ●", ""),
        items="months",
        on_click=on_month_selected
    ),
    width=4
)


prod_scroller = ScrollingGroup(
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
        # Button(
        #     text=Const("📊 Текущие данные"), 
        #     id="start", 
        #     on_click=lambda c, b, m: m.start(state=TrainerStates.select_month)
        # ),
        Button(
            text=Format("📝 Ждут проверки: {count_in_review}"),
            id="In_review",
            when=lambda data, *args: int(data.get("count_in_review", 0)) > 0,
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.reports_child)
        ),
        Button(
            text=Const("📜 Смотреть историю"),
            id="history",
            on_click=lambda c, b, m: m.start(state=ProgressHistory.history_menu)
        ),
        state=DirectorState.director_menu,
        getter=get_count_in_review
    ),
    Window(
        Const("👶📊 Выберите ребёнка для проверки отчёта"),
        prod_scroller,
        Row(
            PrevPage(scroll=prod_scroller, text=Format("◀️")),
            NextPage(scroll=prod_scroller, text=Format("▶️"))
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.back()
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
            "🏆 <b>Уровень:</b> {level}\n\n"
            "🏋️ <b>Тренер:</b> {trainer_username}\n"
            "👨‍👩‍👧 <b>Родитель:</b> {parent_username}\n\n"
            "📅 <b>ОФП</b> \n\n{month_plan}"
        ),
        months_select,
        Button(
            text=Const("🔍 Смотреть отчёт"),
            id="check_report",
            when=lambda data, widget, manager: data.get("count_rows", 0) > 0,
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.select_elements_in_review)
        ),
        Row(
            Button(
                text=Const("✅ Утвердить"),
                id="approve",
                on_click=lambda c, b, m: m.switch_to(state=DirectorState.agree_to_approve_report)
            ),
            Button(
                text=Const("❌ Отклонить"),
                id="reject",
                on_click=lambda c, b, m: m.switch_to(state=DirectorState.reject_report)
            ),
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.reports_child)
        ),
        state=DirectorState.report,
        getter=get_report_card,
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
            on_click=lambda c, b, m: m.back()
        ),
        state=DirectorState.select_elements_in_review,
        getter=get_exercise_btn
    ),
    Window(
        Format("{text}"),
        DynamicMedia("photo"),
        # Row(
        #     Button(text=Const("◀️"), id="prev", on_click=prev_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
        #     Button(text=Const("▶️"), id="next", on_click=next_history, when=lambda data, widget, manager: data.get("text") != "Нет данных"),
        # ),
        Button(
            text=Const("📸 Изменить фото"),
            id="edit_photo",
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.edit_photo_in_review),
        ),
        Button(
            text=Const("📝 Изменить комментарий"),
            id="edit_comment",
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.edit_comment_in_review),
            when=lambda data, widget, manager: data.get("text") != "Нет данных" and data.get("has_comment"),
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(state=DirectorState.select_elements_in_review)
        ),
        state=DirectorState.history_progress,
        getter=get_current_history_item
    ),
    Window( # Изменение комментария отчета в статусе "На проверке"
        Const(
            "✍️ Отправьте текст комментария.\n\n"
            "➡️ Просто напишите сообщение ниже, и оно сохранится к отчёту."
          ),
        MessageInput(
            on_edit_comment,
            content_types=ContentType.TEXT
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(DirectorState.history_progress)
        ),
        state=DirectorState.edit_comment_in_review
    ),
    Window( # Изменение фото отчета в статусе "На проверке"
        Const(
            "✍️ Отправьте новое фото.\n\n"
            "➡️ Оно автоматически изменится в отчёте."
          ),
        MessageInput(
            on_edit_photo,
            content_types=ContentType.PHOTO
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back_menu",
            on_click=lambda c, b, m: m.switch_to(DirectorState.history_progress)
        ),
        state=DirectorState.edit_photo_in_review
    ),
    Window(
        Const(
            "<b>Вы уверены, что хотите УТВЕРДИТЬ этот отчёт?</b>\n\n"
            "После утверждения:\n"
            "• отчёт будет сгенерирован в PDF формате;\n"
            "• вам и родителю будет отправлен отчёт.\n"
        ),
        Row(
            Button(
                text=Const("✅ Да"),
                id="yes_approve",
                on_click=approve_report
            ),
            Button(
                text=Const("❌ Нет"),
                id="no_approve",
                on_click=lambda c, b, m: m.switch_to(state=DirectorState.report)
            ),
        ),
        state=DirectorState.agree_to_approve_report
    ),
    Window(
        Const(
            "<b>Вы уверены, что хотите ОТКЛОНИТЬ этот отчёт?</b>\n\n"
            "После отклонения:\n"
            "• отчёт вернётся в статус «Создан»;\n"
            "• тренеру придёт уведомление о том, что отчёт за месяц отклонён.\n"
        ),
        Row(
            Button(
                text=Const("✅ Да"),
                id="yes_approve",
                on_click=reject_report
            ),
            Button(
                text=Const("❌ Нет"),
                id="no_approve",
                on_click=lambda c, b, m: m.switch_to(state=DirectorState.report)
            ),
        ),
        state=DirectorState.reject_report
    )
)