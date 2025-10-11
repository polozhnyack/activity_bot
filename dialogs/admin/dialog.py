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
                text=Const("🛡 Выдать роль"),
                id="grant_role"
            ),
            Button(
                text=Const("❌ Забрать роль"),
                id="revoke_role"
            ),
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
    
)
