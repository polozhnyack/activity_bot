import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Date, Text, BigInteger, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base
from typing import Optional

from utils import generate_child_code

Base = declarative_base()

# --- Enums ---
class UserRole(enum.Enum):
    parent = "parent"
    trainer = "trainer"
    director = "director"
    director_novice = "director_novice"
    director_pro = "director_pro"
    admin = "admin"


ROLE_NAMES = {
    UserRole.parent: "👨‍👩‍👧 Родитель",
    UserRole.trainer: "💪 Тренер",
    UserRole.director_novice: "🎓 Директор (новички)",
    UserRole.director_pro: "🏆 Директор (PRO)",
    UserRole.admin: "🛠 Администратор",
}


class ReportStatus(enum.Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"

# --- Models ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    children: Mapped[list["Child"]] = relationship("Child", back_populates="parent")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="author")


class Child(Base):
    __tablename__ = "children"

    code: Mapped[str] = mapped_column(String(12), primary_key=True, unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    level_id: Mapped[Optional[int]] = mapped_column(ForeignKey("levels.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    parent: Mapped["User"] = relationship("User", back_populates="children")
    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="children")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="child")

    def __init__(self, **kwargs):
        if "code" not in kwargs:
            kwargs["code"] = generate_child_code()
        super().__init__(**kwargs)



class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[str] = mapped_column(ForeignKey("children.code"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # формат "YYYY-MM"
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.draft)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    director_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    child: Mapped["Child"] = relationship("Child", back_populates="reports")
    photos: Mapped[list["Photo"]] = relationship("Photo", back_populates="report")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="report")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Telegram file_id
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    report: Mapped["Report"] = relationship("Report", back_populates="photos")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    report: Mapped["Report"] = relationship("Report", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level_id: Mapped[Optional[int]] = mapped_column(ForeignKey("levels.id"), nullable=True)

    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="exercises")


class MonthlyPlan(Base):
    __tablename__ = "monthly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    child_id: Mapped[str] = mapped_column(ForeignKey("children.code"), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    notes: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    children: Mapped[list["Child"]] = relationship("Child", back_populates="level")
    exercises: Mapped[list["Exercise"]] = relationship("Exercise", back_populates="level")


ROLE_LEVEL_IDS_MAP = {
    UserRole.director_novice: [3, 4],
    UserRole.director_pro: [2],
}



class ActivityEventType(enum.Enum):
    photo_uploaded = "photo_uploaded"
    comment_added = "comment_added"
    report_created = "report_created"
    report_in_review = "report_in_review"
    report_sent = "report_sent"
    ofp_added = "ofp_added"
    photo_edit = "photo_edit"
    approve_report = "approve_report"
    create_child = "create_child"
    delete_child = "delete_child"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Ребёнок
    child_id: Mapped[str] = mapped_column(
        ForeignKey("children.code"),
        nullable=False,
        index=True,
    )

    # Тип события
    event_type: Mapped[ActivityEventType] = mapped_column(
        Enum(ActivityEventType),
        nullable=False,
        index=True,
    )

    # photo.id / comment.id / report.id
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Кто совершил действие
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    actor_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
    )
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        index=True,
    )

    child: Mapped["Child"] = relationship("Child")
    actor: Mapped["User"] = relationship("User")
