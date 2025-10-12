from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, CallbackQuery, Chat
from aiogram.types import ContentType, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser, ReplyKeyboardRemove

from aiogram_dialog.widgets.kbd import Select

from dialogs.states import *
from aiogram_dialog.widgets.input import MessageInput

from models.methods import UserService, ChildService
from models.models import *
from config import load_config
from logger import logger


async def creator_child(callback: CallbackQuery, button, dialog_manager: DialogManager):
    params = callback.data.split("_")
    param = params[0]
    
    logger.debug(param)

    dialog_manager.dialog_data["param"] = param
    await dialog_manager.switch_to(state=AdminState.child_create_or_delete)


async def child_handler(
        message: Message,
        message_input: MessageInput,
        dialog_manager: DialogManager,
        **kwargs
):
    param = dialog_manager.dialog_data.get("param")
    child_service: ChildService = dialog_manager.middleware_data["ChildService"]

    input_text = message.text.strip()

    if param == "create":
        parts = input_text.split(",")
        if len(parts) < 2:
            await message.answer("❌ Нужно ввести ФИ и дату рождения через запятую (например: Иван Иванов, 11.11.2011)")
            return
        full_name = parts[0].strip()
        from datetime import datetime
        try:
            birth_date = datetime.strptime(parts[1].strip(), "%d.%m.%Y").date()
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ДД.MM.ГГГГ")
            return

        child = await child_service.create(full_name=full_name, birth_date=birth_date)
        await message.answer(f"✅ Ребёнок создан: {child.full_name} ({child.code})")

    elif param == "delete":
        child_code = input_text
        success = await child_service.delete_by_code(child_code)
        if success:
            await message.answer(f"✅ Ребёнок {child_code} удалён")
        else:
            await message.answer(f"❌ Ребёнок {child_code} не найден")

    await dialog_manager.switch_to(AdminState.admin_menu)



async def user_contact_handler(
        message: Message,
        message_input: MessageInput,
        dialog_manager: DialogManager,
        **kwargs
):
    
    logger.debug("Запущен user_contact_handler")
    user_service: UserService = dialog_manager.middleware_data["UserService"]

    if message.user_shared:
        user_id = message.user_shared.user_id
        selected_role = dialog_manager.dialog_data.pop("selected_role", None)

        if not selected_role:
            await message.answer("❌ Роль не выбрана.")
            return

        updated = await user_service.update_role(
            user_id=user_id,
            new_role_str=selected_role
        )

        if updated:
            chat: Chat = await message.bot.get_chat(user_id)
            full_name = getattr(chat, "full_name", f"ID {user_id}")
            await message.answer(
                f"✅ Пользователю {full_name} успешно присвоена роль: {selected_role.capitalize()}"
            )
        else:
            await message.answer(
                f"❌ Не удалось изменить роль пользователя с ID {user_id}. Возможно, роль некорректна или пользователь не найден."
            )
    else:
        await message.answer("❌ Не удалось получить информацию о пользователе.")

    await dialog_manager.switch_to(AdminState.admin_menu)


keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="Отправить пользователя 👀",
                request_user=KeyboardButtonRequestUser(
                    request_id=123,
                    user_is_bot=False
                )
            )
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


async def on_role_selected(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    
    message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text="📁",
        reply_markup=keyboard
    )
    
    manager.dialog_data["pupa"] = message.message_id
    manager.dialog_data["selected_role"] = item_id

    await callback.answer(f"✅ Вы выбрали роль: {item_id}")
    await manager.switch_to(AdminState.user_select)


async def go_back_admin_menu(callback: CallbackQuery, button, dialog_manager: DialogManager):
    pupa = dialog_manager.dialog_data.get("pupa")
    if pupa:
        try:
            message = await callback.message.answer(
                text=callback.message.text or "🔄",
                reply_markup=ReplyKeyboardRemove()
            )

            await message.delete()

            await callback.bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=pupa
            )

        except Exception as e:
            message = await callback.message.answer(
                "🔄",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.delete()

    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(state=AdminState.admin_menu)

