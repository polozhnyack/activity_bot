from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import case, update, delete, select, exists, func
from sqlalchemy.exc import IntegrityError

from typing import List, Union, Optional
from collections import defaultdict

from .models import *
from utils import generate_child_code


@dataclass
class UserService:
    session: AsyncSession

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_child_by_parent_id(self, parent_id: int) -> Child | None:
        result = await self.session.execute(
            select(Child).where(Child.parent_id == parent_id)
        )
        return result.scalar_one_or_none()

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
            return "not_found"
        

        if child.parent_id is not None:
            return "already_attached"

        child.parent_id = parent_id
        self.session.add(child)
        await self.session.commit()
        return "attached"
    

    async def get_by_parent_id(self, parent_id: int) -> Optional["Child"]:
        result = await self.session.execute(select(Child).where(Child.parent_id == parent_id))
        return result.scalars().first()
    

    async def update_role(self, user_id: int, new_role_str: str) -> bool:

        new_role = UserRole(new_role_str)

        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if not user:
            return False

        if user.role == new_role:
            return True

        user.role = new_role
        self.session.add(user)
        await self.session.commit()
        return True

    

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


    async def delete_by_code(self, child_code: str) -> bool:
        result = await self.session.execute(select(Child).where(Child.code == child_code))
        child = result.scalars().first()
        if not child:
            return False

        await self.session.execute(delete(Comment).where(Comment.report_id.in_(
            select(Report.id).where(Report.child_id == child_code)
        )))

        await self.session.execute(delete(Photo).where(Photo.report_id.in_(
            select(Report.id).where(Report.child_id == child_code)
        )))

        await self.session.execute(delete(Report).where(Report.child_id == child_code))

        await self.session.execute(delete(MonthlyPlan).where(MonthlyPlan.child_id == child_code))

        await self.session.delete(child)

        await self.session.commit()
        return True


    async def get_children_with_reports_in_review(self):
        stmt = (
            select(Child)
            .join(Report, Report.child_id == Child.code)
            .where(Report.status == ReportStatus.in_review)
            .distinct()
        )
        result = await self.session.scalars(stmt)
        return result.all()


    async def get_monthly_plan(self, child_id: str, month: str | None = None):
        query = select(MonthlyPlan).where(MonthlyPlan.child_id == child_id)
        if month:
            query = query.where(MonthlyPlan.month == month)

        result = await self.session.execute(query)
        plans = result.scalars().all()
        return plans
    

    async def set_monthly_plan(self, child_id: str, month: str, notes: str):
        query = await self.session.execute(
            select(MonthlyPlan).where(MonthlyPlan.child_id == child_id, MonthlyPlan.month == month)
        )
        plan = query.scalar_one_or_none()

        if plan:
            plan.notes = notes
            plan.updated_at = datetime.now()
        else:
            plan = MonthlyPlan(child_id=child_id, month=month, notes=notes)
            self.session.add(plan)

        await self.session.commit()
        return plan

            


@dataclass
class ReportService:
    session: AsyncSession

    async def create_report_photo(
        self,
        user_id: int,
        child_code: str,
        photo_file_id: str,
        trainer_id: int | None = None,
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
            trainer_id=trainer_id
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
        exercise_id: int | None = None,
        status: ReportStatus | None = None
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

        if status is not None:
            stmt = stmt.where(Report.status == status)

        result = await self.session.execute(stmt)
        reports = result.scalars().all()

        for r in reports:
            await self.session.refresh(r, attribute_names=["comments", "photos"])

        return reports
    

    async def get_reports_by_child_and_month_sorted(
        self,
        child_id: str,
        month: str,
        status: ReportStatus | None = None,
    ) -> list[Report]:
        stmt = (
            select(Report)
            .where(Report.child_id == child_id, Report.month == month)
            .options(
                selectinload(Report.photos),
                selectinload(Report.comments).joinedload(Comment.author),
                joinedload(Report.child),
            )
            .order_by(Report.id.asc())
        )

        if status is not None:
            stmt = stmt.where(Report.status == status)

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
    

    async def send_reports_to_review(
        self,
        child_id: str,
        month: str,
        trainer_id: int,
    ) -> Union[bool, str]:
        """
        Проверяет, что у ребёнка за указанный месяц:
        - каждый отчёт содержит ровно одно фото;
        - у каждого фото есть exercise_id;
        - нет дубликатов упражнений.
        """

        result = await self.session.execute(
            select(Report)
            .options(joinedload(Report.photos).joinedload(Photo.exercise))
            .where(
                Report.child_id == child_id,
                Report.month == month,
                Report.status == ReportStatus.draft
                )
        )
        reports = result.unique().scalars().all()

        if not reports:
            return "❌ У ребёнка нет отчётов за этот месяц."

        seen_exercises = set()

        for report in reports:
            photos = report.photos

            if len(photos) != 1:
                return f"❌ В отчёте {report.id} должно быть ровно одно фото, найдено {len(photos)}."

            photo = photos[0]

            if not photo.exercise_id:
                return f"❌ Фото в отчёте {report.id} не привязано к упражнению."

            if photo.exercise_id in seen_exercises:
                return f"❌ Найдено больше одного фото для упражнения '{photo.exercise.name}'. Допускается только одно."
            
            seen_exercises.add(photo.exercise_id)

        await self.session.execute(
            update(Report)
            .where(Report.child_id == child_id, Report.month == month)
            .values(status=ReportStatus.in_review, trainer_id=trainer_id)
            .execution_options(synchronize_session="fetch")
        )

        await self.session.commit()
        return True

        
    
    async def get_reports_in_review_count(self) -> int:
        stmt = select(func.count()).select_from(Report).where(Report.status == ReportStatus.in_review)
        result = await self.session.execute(stmt)
        return result.scalar_one()


    async def get_reports_grouped_review(self, child_id: str):
        result = await self.session.execute(
            select(Report)
            .where(
                Report.child_id == child_id,
                Report.status == ReportStatus.in_review
            )
        )
        reports = result.scalars().all()

        grouped = defaultdict(list)
        for report in reports:
            grouped[report.month].append(report)

        return dict(grouped)
    

    async def get_months_in_review(self, child_id: str) -> list[str]:
        result = await self.session.execute(
            select(Report.month)
            .where(
                Report.child_id == child_id,
                Report.status == ReportStatus.in_review
            )
            .distinct()
            .order_by(Report.month.asc())
        )
        return [row[0] for row in result.all()]
    

    async def get_child_reports_json(self, child_id: str) -> dict:
        result = await self.session.execute(
            select(Report)
            # .where(Report.child_id == child_id, Report.status == ReportStatus.approved)
            .where(Report.child_id == child_id, Report.status == ReportStatus.in_review)
            .options(
                selectinload(Report.photos).selectinload(Photo.exercise),
                selectinload(Report.comments)
            )
        )
        reports = result.scalars().all()
        data = {}

        for report in reports:
            month = report.month
            if month not in data:
                data[month] = {}

            for photo in report.photos:
                exercise_name = photo.exercise.name if photo.exercise else "Без упражнения"
                if exercise_name not in data[month]:
                    data[month][exercise_name] = []

                related_comments = [
                    c.text for c in report.comments
                ]

                data[month][exercise_name].append({
                    "file_id": photo.file_id,
                    "comments": related_comments
                })
        return data


    async def reset_reports_to_draft(self, child_code: str, selected_month: str):

        stmt = (
            select(Report)
            .join(Report.child)
            .where(Child.code == child_code, Report.month == selected_month)
        )
        result = await self.session.execute(stmt)
        reports = result.scalars().all()

        if not reports:
            return False, None

        trainer_ids = {r.trainer_id for r in reports if r.trainer_id is not None}

        if len(trainer_ids) != 1:
            return False, None

        trainer_id = trainer_ids.pop()

        for report in reports:
            report.status = ReportStatus.draft

        await self.session.commit()
        return True, trainer_id



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