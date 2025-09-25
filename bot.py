import asyncio
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import Config, load_config
from aiogram_dialog import setup_dialogs

from logger import logger

from middlewares.session import DbSessionMiddleware
# from middlewares.logging import UpdateLoggerMiddleware

from dialogs.main_menu.dialog import start_menu
from dialogs.main_menu.handlers import router
from dialogs.materials.dialog import materials
from dialogs.materials.handlers import router as answer_router
from dialogs.catalog.dialog import shop
from dialogs.catalog.handlers import router as payment_router
from dialogs.admin.dialog import admin as admin_panel


async def create_tables(url):
    from models.models import Base
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

async def main():
    config: Config = load_config()

    await create_tables(config.db.url)
    engine = create_async_engine(url = config.db.url, echo = False)
    sessionmaker = async_sessionmaker(engine, expire_on_commit = False)

    bot = Bot(
        token = config.tg_bot.token,
        default = DefaultBotProperties(parse_mode = ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(session_pool = sessionmaker))
    dp.update.outer_middleware(UpdateLoggerMiddleware())


    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_router(payment_router)
    dp.include_router(router)
    dp.include_router(answer_router)

    dp.include_router(shop)
    dp.include_router(materials)
    dp.include_router(start_menu)
    dp.include_router(admin_panel)


    setup_dialogs(dp)

    logger.info("Запуск бота")

    await dp.start_polling(bot, allowed_updates = dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())