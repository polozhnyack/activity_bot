from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import async_sessionmaker
from models.methods import UserService, ChildService, ExerciseService, ReportService

import json

from logger import logger


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            data["UserService"] = UserService(session)
            data["ChildService"] = ChildService(session)
            data["ExerciseService"] = ExerciseService(session)
            data["ReportService"] = ReportService(session)

            return await handler(event, data)


class UpdateLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            if event.message:
                user = event.message.from_user
                logger.info(f"📩 NEW MESSAGE from {user.id} ({user.username}): {event.message.text}")
            elif event.callback_query:
                user = event.callback_query.from_user
                logger.info(f"📩 CALLBACK from {user.id} ({user.username}): {event.callback_query.data}")
            else:
                logger.info(f"📩 Update type: {event.update_type}")
        except Exception:
            logger.info(f"📩 Update: {event}")

        return await handler(event, data)