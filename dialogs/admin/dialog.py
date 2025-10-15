from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row, Select, Group, PrevPage, NextPage, ScrollingGroup, Radio
from aiogram_dialog.widgets.media import StaticMedia, MediaScroll, DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram.types import ContentType

from dialogs.states import AdminState
from .handlers import *
from .getter import *

from config import load_config
from dialogs.trainer.getter import get_childs_btn, months_getter, get_childs_in_review_btn, get_exercise_btn


admin_window = Dialog(
    Window(
        Const("Роль: Администратор.\nВыберите действие:"),
        Row(
            Button(
                text=Const("➕ Создать ребенка"),
                id="create_child",
                on_click=creator_child,
            ),
            Button(
                text=Const("➖ Удалить ребенка"),
                id="delete_child",
                on_click=creator_child
            ),
        ),
        Row(
            Button(
                text=Const("🛡 Изменить роль"),
                id="edit_role",
                on_click=lambda c, b, m: m.switch_to(state=AdminState.role_select)
            ),
        ),
        Button(
            text=Const("📜 Смотреть историю"),
            id="history",
            on_click=lambda c, b, m: m.start(state=ProgressHistory.history_menu)
        ),
        Button(
            text=Const("🔍 Список кодов детей"),
            id="child_codes",
            on_click=export_children_to_excel
        ),
        state=AdminState.admin_menu
    ),
    Window(
        Format("{child_create_or_delete_text}"),
        MessageInput(
            child_handler,
            content_types=ContentType.TEXT
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(state=AdminState.admin_menu),
        ),
        state=AdminState.child_create_or_delete,
        getter=child_create_delete_getter
    ),
    Window(
        Format("{role_editor_text}"),
        Group(
            Select(
                Format("{item[0]}"),
                id="select_role",
                item_id_getter=lambda x: x[1],
                items="roles",
                on_click=on_role_selected,
            ),
            width=1,
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(state=AdminState.admin_menu),
        ),
        getter=get_roles_data,
        state=AdminState.role_select,
    ),
    Window(
        Const("Отправьте пользователя по кнопке 👇"),
        MessageInput(
            user_contact_handler,
        ),
        Button(
            text=Const("⬅️ Назад"),
            id="back",
            on_click=go_back_admin_menu,
        ),
        state=AdminState.user_select
    )

)
