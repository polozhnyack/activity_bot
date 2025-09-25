from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy import case, update, delete


from typing import List, Union, Optional

from .models import *


@dataclass
class UserService:
    session: AsyncSession

    async def create_user(self, user_id: int, full_name: str, role: UserRole) -> User:
        user = User(telegram_id=user_id, full_name=full_name, role=role)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user