import asyncio
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import Config, load_config
from aiogram_dialog import setup_dialogs

from logger import logger

from middleware.session import DbSessionMiddleware, UpdateLoggerMiddleware


from dialogs.main.handlers import router
from dialogs.main.dialog import parent_reg, child_info_dialog
from dialogs.trainer.dialog import trainer_dialog, progress_history
from dialogs.director.dialog import director_dialog
from dialogs.admin.dialog import admin_window


async def create_tables(url):
    from models.models import Base
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

async def main():
    config: Config = load_config()

    await create_tables(config.db.url)
    engine = create_async_engine(url = config.db.url, echo = False, pool_pre_ping=True, pool_recycle=1800)
    sessionmaker = async_sessionmaker(engine, expire_on_commit = False)

    bot = Bot(
        token = config.tg_bot.token,
        default = DefaultBotProperties(parse_mode = ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(session_pool = sessionmaker))
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.update.outer_middleware(UpdateLoggerMiddleware())

    dp.include_router(router)
    dp.include_router(parent_reg)

    dp.include_router(child_info_dialog)
    dp.include_router(trainer_dialog)
    dp.include_router(director_dialog)
    dp.include_router(admin_window)
    dp.include_router(progress_history)

    setup_dialogs(dp)

    logger.info("Запуск бота")

    await dp.start_polling(bot, allowed_updates = dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())