from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import ChildInfo, ParentRegistration
from .handlers import *
from .getter import *
from config import load_config

config = load_config()


parent_reg = Dialog(
    Window(
        Const("Введите уникальный код вашего ребенка."),
        MessageInput(
            child_code_handler,
            content_types=ContentType.TEXT
        ),
        state=ParentRegistration.input_code
    )
)


child_info_dialog=Dialog(
    Window(
        Format(
            "ФИО: {child_name}\n"
            "Дата рождения: {child_birth_date}"
        ),
        Button(
            text=Const("Загрузить фото"),
            id="send_data",
            on_click=lambda c, b, m: m.switch_to(state=ChildInfo.select_month)
        ),
        state=ChildInfo.start_info,
        getter=get_child_info
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
        state=ChildInfo.select_month,
        getter=months_getter
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
            id="back",
            on_click=back_btn
        ),
        state=ChildInfo.select_sports_item,
        getter=get_exercise_btn
    ),
    Window(
        Format("Элемент: <b>{element_name}</b>\n\nОтправьте фото для отчета."),
        MessageInput(
            on_photo_input,
            content_types=ContentType.PHOTO
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back",
            on_click=back_btn
        ),
        state=ChildInfo.wait_photo,
        getter=get_exercise_text
    )

)