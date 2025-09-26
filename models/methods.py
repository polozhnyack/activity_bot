from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy import case, update, delete, select
from sqlalchemy.exc import IntegrityError

from typing import List, Union, Optional

from .models import *
from utils import generate_child_code


@dataclass
class UserService:
    session: AsyncSession

    async def create_user(self, user_id: int, full_name: str, role: UserRole) -> User:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(id=user_id, full_name=full_name, role=role)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    

    async def attach_to_parent(self, parent_id: int, child_code: str) -> bool:
        result = await self.session.execute(
            select(Child).where(Child.code == child_code)
        )
        child = result.scalars().first()
        if not child:
            return False


        child.parent_id = parent_id
        self.session.add(child)
        await self.session.commit()
        return True
    

    async def get_by_parent_id(self, parent_id: int) -> Optional["Child"]:
        result = await self.session.execute(select(Child).where(Child.parent_id == parent_id))
        return result.scalars().first()
    

@dataclass
class ChildService:
    session: AsyncSession

    async def get_by_code(self, code: str) -> Optional["Child"]:
        result = await self.session.execute(select(Child).where(Child.code == code))
        return result.scalars().first()
    
    async def create(self, **kwargs) -> "Child":
        for _ in range(10):
            code = generate_child_code()

            result = await self.session.execute(select(Child).where(Child.code == code))
            if not result.scalars().first():
                child = Child(code=code, **kwargs)
                self.session.add(child)
                try:
                    await self.session.commit()
                except IntegrityError:
                    await self.session.rollback()
                    continue
                return child