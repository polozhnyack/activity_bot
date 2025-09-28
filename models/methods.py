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

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

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

    async def get_all(self) -> list["Child"]:
        result = await self.session.execute(select(Child))
        return result.scalars().all()

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
            


@dataclass
class ReportService:
    session: AsyncSession

    async def create_report_photo(
        self,
        user_id: int,
        child_code: str,
        photo_file_id: str,
        exercise_id: int | None = None,
        month: int | None = None
    ):
        year = datetime.now().year
        month_str = f"{year}-{month:02d}" if month else datetime.now().strftime("%Y-%m")

        report = Report(
            child_id=child_code,
            month=month_str,
            status=ReportStatus.draft,
        )
        self.session.add(report)
        await self.session.flush()

        photo = Photo(
            report_id=report.id,
            file_id=photo_file_id,
            exercise_id=exercise_id,
            uploaded_by=user_id
        )
        self.session.add(photo)

        await self.session.commit()
        await self.session.refresh(report)
        return report
    
    async def get_reports_info(
        self, child_code: str, month: str | None = None
    ) -> dict:
        if not month:
            month = datetime.now().strftime("%Y-%m")

        stmt = (
            select(Report)
            .where(Report.child_id == child_code)
            .where(Report.month == month)
            .order_by(Report.created_at.desc())
        )
        result = await self.session.execute(stmt)
        reports: list[Report] = result.scalars().all()

        last_report_date = (
            reports[0].created_at.strftime("%d.%m.%Y") if reports else "—"
        )

        return {
            "reports": reports,
            "last_report_date": last_report_date,
        }



@dataclass
class ExerciseService:
    session: AsyncSession

    async def get_all(self) -> list["Exercise"]:
        result = await self.session.execute(select(Exercise))
        return result.scalars().all()
    
    
    async def get_exercise_name_by_id(self, exercise_id: int) -> str | None:
        result = await self.session.execute(
            select(Exercise.name).where(Exercise.id == exercise_id)
        )
        exercise_name = result.scalar_one_or_none()
        return exercise_name