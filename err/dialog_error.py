from aiogram_dialog.api.exceptions import UnknownIntent
from aiogram.fsm.context import FSMContext
from dialogs.states import Err
from aiogram_dialog import DialogManager, StartMode
from aiogram import types
from aiogram import Router

from aiogram.exceptions import TelegramAPIError
from sqlalchemy.exc import SQLAlchemyError
from logger import logger


router = Router()


@router.errors()
async def handle_global_errors(exception: Exception, dialog_manager: DialogManager):
    logger.error(f"Перехвачено исключение: {type(exception)} — {exception}")

    if isinstance(exception, types.error_event.ErrorEvent):
        logger.warning("Ошибка связана с событием.")

        if isinstance(exception.exception, UnknownIntent):
            logger.info("Перехвачен UnknownIntent: стек диалога потерян, откатываем в начальное состояние.")
            try:
                await dialog_manager.start(state=Err.err, mode=StartMode.RESET_STACK)
            except Exception as e:
                logger.critical(f"Не удалось перейти в главное меню после UnknownIntent: {e}")
        else:
            import traceback
            tb_str = "".join(traceback.format_exception(type(exception.exception), exception.exception, exception.exception.__traceback__))
            logger.error(f"Неизвестная ошибка события:\n{tb_str}")

    elif isinstance(exception, SQLAlchemyError):
        logger.error(f"Ошибка базы данных: {exception}")

    elif isinstance(exception, TelegramAPIError):
        logger.warning(f"Проблема с Telegram API: {exception}")

    elif isinstance(exception, TypeError) and "int()" in str(exception):
        logger.warning("Типовая ошибка: попытка преобразовать None в int")

    else:
        logger.exception("Необработанная ошибка в приложении", exc_info=exception)

