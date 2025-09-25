from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

from aiogram_dialog.widgets.kbd import Button

from sqlalchemy.ext.asyncio import AsyncSession

import re
import time
import json

from dialogs.states import MainMenu, UserMaterials, Shop, AdminPanel

from models.methods import UserService
from models.methods import UserLoader, ConferenceLoader
from models.models import *
from config import load_config
from logger import logger

router = Router()
config = load_config()

@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager, state: FSMContext, user_service: UserService):

    await user_service.create_user(
        user_id = message.from_user.id, 
        full_name=message.from_user.full_name,
        role=UserRole.parent
    )

    await state.clear()

    await dialog_manager.reset_stack()
    await dialog_manager.start(state=MainMenu.start_user, mode=StartMode.RESET_STACK)