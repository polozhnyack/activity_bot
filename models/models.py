from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, BigInteger, TIMESTAMP, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()



import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Date, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base

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

    id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    children: Mapped[list["Child"]] = relationship("Child", back_populates="parent")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="author")


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[date] = mapped_column(Date)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parent: Mapped["User"] = relationship("User", back_populates="children")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="child")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), nullable=False)
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
    exercise_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report: Mapped["Report"] = relationship("Report", back_populates="photos")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report: Mapped["Report"] = relationship("Report", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
