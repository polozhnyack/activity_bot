from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Column, Button, Url, Row
from aiogram_dialog.widgets.media import StaticMedia
from aiogram.types import ContentType

from dialogs.states import MainMenu
from .handlers import *
from config import load_config

config = load_config()


main_menu = Dialog(
    Window(
        Const("Введите уникальный код вашего ребенка."),
        state=MainMenu.start_user
    ),
)



