from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import case, update, delete, select, exists
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
        month: int | None = None,
        comment_text: str | None = None  # новый параметр для комментария
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

        if comment_text:
            comment = Comment(
                report_id=report.id,
                author_id=user_id,
                text=comment_text
            )
            self.session.add(comment)

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
    

    async def get_reports_by_child_and_month(
        self,
        child_id: str,
        month: str,
        exercise_id: int | None = None
    ) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.child_id == child_id, Report.month == month)
            .options(
                selectinload(Report.photos),
                selectinload(Report.comments).joinedload(Comment.author),
                joinedload(Report.child),
            )
        )

        if exercise_id is not None:
            stmt = stmt.where(
                exists().where(
                    (Photo.report_id == Report.id) &
                    (Photo.exercise_id == exercise_id)
                )
            )

        result = await self.session.execute(stmt)
        reports = result.scalars().all()

        for r in reports:
            await self.session.refresh(r, attribute_names=["comments", "photos"])

        return reports
    

    async def add_comment(self, report_id: int, author_id: int, text: str) -> Comment:
        result = await self.session.execute(
            select(Report)
            .where(Report.id == report_id)
            .options(selectinload(Report.comments))
        )
        report = result.scalar_one_or_none()
        if not report:
            raise ValueError(f"Report {report_id} not found")

        for old_comment in report.comments:
            await self.session.delete(old_comment)

        comment = Comment(
            report_id=report_id,
            author_id=author_id,
            text=text,
            created_at=datetime.now()
        )

        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        return comment
    

    async def delete_report(self, child_id: str, month: str, report_id: int) -> bool:
        """
        Удаляет отчет по child_id, month и report_id.
        Возвращает True, если отчет был найден и удален, False иначе.
        """
        result = await self.session.execute(
            select(Report)
            .where(
                Report.id == report_id,
                Report.child_id == child_id,
                Report.month == month
            )
            .options(
                selectinload(Report.photos),
                selectinload(Report.comments)
            )
        )
        report = result.scalar_one_or_none()
        if not report:
            return False

        for photo in report.photos:
            await self.session.delete(photo)
        for comment in report.comments:
            await self.session.delete(comment)

        await self.session.delete(report)
        await self.session.commit()

        return True






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