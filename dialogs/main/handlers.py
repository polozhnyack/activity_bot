from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

from aiogram_dialog.widgets.kbd import Button

from sqlalchemy.ext.asyncio import AsyncSession

from dialogs.states import *

from models.methods import UserService, ChildService
from models.models import *
from config import load_config
from logger import logger

router = Router()
config = load_config()

@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager, state: FSMContext, UserService: UserService):

    await UserService.create_user(
        user_id = message.from_user.id, 
        full_name=message.from_user.full_name,
        role=UserRole.parent
    )

    await state.clear()

    await dialog_manager.reset_stack()
    await dialog_manager.start(state=ParentRegistration.input_code, mode=StartMode.RESET_STACK)


async def child_code_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager,
        **kwargs
):
    child_service: ChildService = manager.middleware_data["ChildService"]
    user_service: UserService = manager.middleware_data["UserService"]

    child: Child = await child_service.get_by_code(message.text.strip())

    if child:
        await user_service.attach_to_parent(
            parent_id=message.from_user.id,
            child_code=message.text.strip()
        )

        manager.dialog_data.update({
            "parent_id": message.from_user.id,
            "child_code": child.code,
            "child_name": child.full_name,
            "child_birth_date": child.birth_date,
        })
        
        await manager.start(
            state=ChildInfo.start_info,
            data=manager.dialog_data
        )
    
    else:
        await message.answer("❌ Неверный код, попробуйте снова.")
        await manager.switch_to(ParentRegistration.input_code)
