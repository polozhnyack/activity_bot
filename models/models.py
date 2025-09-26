import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Date, Text, BigInteger
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
    admin = "admin"

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    children: Mapped[list["Child"]] = relationship("Child", back_populates="parent")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="author")


class Child(Base):
    __tablename__ = "children"

    code: Mapped[str] = mapped_column(String(12), primary_key=True, unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parent: Mapped["User"] = relationship("User", back_populates="children")
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
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    director_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    child: Mapped["Child"] = relationship("Child", back_populates="reports")
    photos: Mapped[list["Photo"]] = relationship("Photo", back_populates="report")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="report")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Telegram file_id
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report: Mapped["Report"] = relationship("Report", back_populates="photos")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report: Mapped["Report"] = relationship("Report", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
