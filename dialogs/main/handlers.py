from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

from aiogram_dialog.widgets.kbd import Button, Select

from sqlalchemy.ext.asyncio import AsyncSession

from dialogs.states import *

from models.methods import UserService, ChildService, ReportService
from models.models import *
from config import load_config
from logger import logger

router = Router()
config = load_config()

@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager, state: FSMContext, UserService: UserService):

    await state.clear()
    await dialog_manager.reset_stack()
    
    user = await UserService.get_by_id(message.from_user.id)

    if user.role != UserRole.parent:
        if user.role == UserRole.trainer:
            await dialog_manager.start(state=TrainerStates.trainer_menu)
        if user.role == UserRole.director:
            await dialog_manager.start(start=DirectorState.director_menu)

    elif user.role == UserRole.parent:
        child = await UserService.get_child_by_parent_id(
            parent_id=message.from_user.id
        )
        await dialog_manager.start(
            state=ChildInfo.start_info,
            data={
                "parent_id": message.from_user.id,
                "child_code": child.code,
                "child_name": child.full_name,
                "child_birth_date": child.birth_date,
            }
        )
    else:
        await UserService.create_user(
            user_id = message.from_user.id, 
            full_name=message.from_user.full_name,
            role=UserRole.parent
        )
        await dialog_manager.start(state=ParentRegistration.input_code, mode=StartMode.RESET_STACK)



async def back_btn(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


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




async def month_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    
    logger.debug(f"Вы выбрали месяц: {item_id}")
    await callback.answer(f"Вы выбрали месяц: {item_id}")
    dialog_manager.dialog_data["selected_month"] = int(item_id)

    logger.debug(dialog_manager.dialog_data)

    await dialog_manager.switch_to(state=ChildInfo.select_sports_item)


async def on_exercise_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,  
):
    logger.debug(f"Вы выбрали упражнение: {item_id}")
    dialog_manager.dialog_data["selected_exercise"] = int(item_id)

    logger.debug(dialog_manager.dialog_data)

    await dialog_manager.switch_to(state=ChildInfo.wait_photo)


async def on_photo_input(message: Message, _: MessageInput, manager: DialogManager):
    if message.media_group_id:
        await message.answer("⚠️ Пожалуйста, отправьте только одно фото.")
        return
    
    photo = message.photo[-1]

    service: ReportService = manager.middleware_data["ReportService"]

    file_id = photo.file_id
    exercise = manager.dialog_data["selected_exercise"]
    month = manager.dialog_data["selected_month"]
    child_code = manager.dialog_data["child_code"]

    if exercise and month and child_code and file_id:
        await service.create_report_photo(
            user_id=message.from_user.id,
            child_code=child_code,
            photo_file_id=file_id,
            exercise_id=exercise,
            month=month
        )

        await message.answer(f"✅ Фото сохранено!")
        await manager.done()

    else: 
        await message.answer(f"❌ <b>Произошла ошибка при сохранении фото!</b>\n\nПопробуйте повторить попытку позже.")