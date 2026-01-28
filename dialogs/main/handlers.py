from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.exceptions import TelegramBadRequest

from aiogram_dialog.widgets.kbd import Button, Select

from sqlalchemy.ext.asyncio import AsyncSession

from dialogs.states import *

from models.methods import UserService, ChildService, ReportService, ActivityLogService
from models.models import *
from config import load_config
from logger import logger
from blockmanager import BlockManager

import asyncio
from collections import defaultdict


router = Router()
config = load_config()
block_manager = BlockManager()

MAX_ATTEMPTS = 3
BLOCK_HOURS = 24


@router.message(CommandStart())
async def command_start_process(
    message: Message,
    dialog_manager: DialogManager,
    state: FSMContext,
    UserService: UserService,
):
    await state.clear()
    await dialog_manager.reset_stack()

    user = await UserService.get_by_id(message.from_user.id)

    if block_manager.is_blocked(message.from_user.id):
        blocked_until = block_manager.get_block_time(message.from_user.id)
        blocked_str = blocked_until.strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"⏳ Вы превысили количество попыток. Повторная попытка возможна после {blocked_str}"
        )
        return
    
    logger.debug("Пользователь не заблокирован!")

    if not user:
        user = await UserService.create_user(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            role=UserRole.parent,
        )
        return await dialog_manager.start(
            state=ParentRegistration.input_code,
            mode=StartMode.RESET_STACK,
        )

    if user.role and user.role != UserRole.parent:
        if user.role == UserRole.trainer:
            await dialog_manager.start(state=TrainerStates.trainer_menu)
        elif user.role in (UserRole.director_novice, UserRole.director_pro):
            await dialog_manager.start(state=DirectorState.director_menu)
        elif user.role == UserRole.admin:
            await dialog_manager.start(state=AdminState.admin_menu)

    elif user.role == UserRole.parent:
        child = await UserService.get_child_by_parent_id(
            parent_id=message.from_user.id
        )
        if child:
            await dialog_manager.start(
                state=ChildInfo.start_info,
                data={
                    "parent_id": message.from_user.id,
                    "child_code": child.code,
                    "child_name": child.full_name,
                    "child_birth_date": child.birth_date,
                },
            )
        else:
            return await dialog_manager.start(
                state=ParentRegistration.input_code,
                mode=StartMode.RESET_STACK,
            )



async def back_btn(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()


async def child_code_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager,
        **kwargs
):
    
    logger.debug("Запуск child_code_handler")
    
    now = datetime.now()
    user_id = message.from_user.id

    if block_manager.is_blocked(user_id):
        blocked_until = block_manager.get_block_time(user_id)
        blocked_str = blocked_until.strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"⏳ Вы превысили количество попыток. Повторная попытка возможна после {blocked_str}"
        )
        return
    
    logger.debug("Пользователь не заблокирован в child_code_handler!")
    
    child_service: ChildService = manager.middleware_data["ChildService"]
    user_service: UserService = manager.middleware_data["UserService"]

    child: Child = await child_service.get_by_code(message.text.strip())

    if child:
        result = await user_service.attach_to_parent(
            parent_id=message.from_user.id,
            child_code=message.text.strip()
        )

        if result == "attached":

            block_manager.reset_attempts(user_id)
            if user_id in block_manager.blocks:
                del block_manager.blocks[user_id]


            
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

        elif result == "already_attached":
            await message.answer("⚠️ Этот ребёнок уже прикреплён к другому родителю.")
            await manager.switch_to(ParentRegistration.input_code)

    else:

        attempts = block_manager.increment_attempts(user_id)
        
        if attempts >= MAX_ATTEMPTS:
            block_manager.block_user(user_id, BLOCK_HOURS)
            await message.answer(
                "❌ Превышено количество попыток. Ввод кода заблокирован на 24 часа."
            )
            await manager.done()
        else:
            await message.answer(f"❌ Неверный код, попробуйте снова. Осталось попыток: {MAX_ATTEMPTS - attempts}")
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


# async def on_photo_input(message: Message, _: MessageInput, manager: DialogManager):
#     # if message.media_group_id:
#     #     await message.answer("⚠️ Пожалуйста, отправьте только одно фото.")
#     #     return
    
#     photo = message.photo[-1]

#     service: ReportService = manager.middleware_data["ReportService"]
#     log_service: ActivityLogService = manager.middleware_data["ActivityLogService"]

#     file_id = photo.file_id
#     exercise = manager.dialog_data["selected_exercise"]
#     month = manager.dialog_data["selected_month"]
#     child_code = manager.dialog_data["child_code"]

#     if exercise and month and child_code and file_id:

#         report = await service.create_report_photo(
#             user_id=message.from_user.id,
#             child_code=child_code,
#             photo_file_id=file_id,
#             exercise_id=exercise,
#             month=month
#         )
#         await message.answer(f"✅ Фото сохранено!")

#         try:
#             await log_service.log(
#                 child_id=child_code,
#                 event_type=ActivityEventType.photo_uploaded,
#                 actor_id=message.from_user.id,
#                 entity_id=report.id
#             )
#         except Exception as e:
#             logger.error(f"Не удалось записать лог фото: {e}")

#         await manager.switch_to(ChildInfo.start_info)
#     else: 
#         await message.answer(f"❌ <b>Произошла ошибка при сохранении фото!</b>\n\nПопробуйте повторить попытку позже.")


# Глобальный счетчик для медиагрупп
media_group_stats = defaultdict(lambda: {'count': 0, 'task': None, 'status_message_id': None, 'next_state': None})

async def on_photo_input(message: Message, _: MessageInput, manager: DialogManager, next_state: type = None):
    storage = manager.middleware_data['fsm_storage']
    key = StorageKey(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        bot_id=manager.event.bot.id
    )
    state = FSMContext(storage=storage, key=key)
    
    data = await state.get_data()

    context = manager.current_context()
    stack_id= context.stack_id
    
    if message.media_group_id:
        group_key = f"{message.from_user.id}_{message.chat.id}_{message.media_group_id}"
        
        media_group_stats[group_key]['count'] += 1
        if next_state:
            media_group_stats[group_key]['next_state'] = next_state
        
        await save_photo(message, manager)
        
        current_group = data.get('current_media_group')
        
        if current_group == message.media_group_id:
            if media_group_stats[group_key]['task']:
                media_group_stats[group_key]['task'].cancel()
            
            media_group_stats[group_key]['task'] = asyncio.create_task(
                send_group_report(
                    group_key=group_key, 
                    message=message, 
                    state=state,
                    manager=manager
                    )
            )
            return
        
        status_msg = await message.bot.send_message(
            chat_id=message.from_user.id,
            text="📤 Начата загрузка альбома..."
            
            )
        media_group_stats[group_key]['status_message_id'] = status_msg.message_id
        
        await state.update_data(current_media_group=message.media_group_id, status_msg_id=status_msg.message_id, stack_id=stack_id, next_state=next_state, dialog_manager=manager)

        logger.debug(status_msg.message_id)
        
        media_group_stats[group_key]['task'] = asyncio.create_task(
            send_group_report(
                group_key=group_key, 
                message=message, 
                state=state, 
                manager=manager,
                status_message_id=status_msg.message_id)
        )
    else:
        await save_photo(message, manager)
        await message.answer("✅ Фото сохранено!")
        if next_state:
            await manager.switch_to(state=next_state)



async def send_group_report(group_key: str, message: Message, state: FSMContext, manager: DialogManager, status_message_id: int = None):
    """Отправляем отчет о сохранении группы фото"""
    await asyncio.sleep(2)

    data = await state.get_data()
    try:
        count = media_group_stats[group_key]['count']
        status_msg_id = data.get("status_msg_id")

        if count > 0:
            if count == 1:
                text = "✅ Фото сохранено!"
            elif count < 5:
                text = f"✅ <b>Сохранено {count} фото!</b>\n\nВы можете продолжить загрузку фото или выйти из режима."
            else:
                text = f"✅ <b>Сохранен альбом из {count} фото!</b>\n\nВы можете продолжить загрузку фото или выйти из режима."
            
            if status_msg_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_msg_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest as e:
                    if "message to edit not found" in str(e) or "message is not modified" in str(e):
                        await message.answer(text)
                        logger.warning(f"status_message_id: {status_msg_id}, {e}")
                    else:
                        raise
            else:
                logger.warning(f"status_message_id: {status_msg_id}")
                await message.answer(text)

        next_state = media_group_stats[group_key].get('next_state')

        if group_key in media_group_stats:
            if media_group_stats[group_key]['task']:
                media_group_stats[group_key]['task'].cancel()
            del media_group_stats[group_key]
        
        await state.update_data(current_media_group=None)
        
    except Exception as e:
        logger.error(f"Ошибка при отправке отчета о медиагруппе: {e}")


async def save_photo(message: Message, manager: DialogManager):
    """Сохраняем фото в БД"""
    service: ReportService = manager.middleware_data["ReportService"]
    log_service: ActivityLogService = manager.middleware_data["ActivityLogService"]
    
    exercise = manager.dialog_data["selected_exercise"]
    month = manager.dialog_data["selected_month"]
    child_code = manager.dialog_data["child_code"]
    
    photo = message.photo[-1]
    report = await service.create_report_photo(
        user_id=message.from_user.id,
        child_code=child_code,
        photo_file_id=photo.file_id,
        exercise_id=exercise,
        month=month
    )
    
    try:
        await log_service.log(
            child_id=child_code,
            event_type=ActivityEventType.photo_uploaded,
            actor_id=message.from_user.id,
            entity_id=report.id
        )
    except Exception as e:
        logger.error(f"Не удалось записать лог фото: {e}")
    
    return report