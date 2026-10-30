"""Persistence needed by the Sprint 2 frontend and the loyalty content editor."""
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.model import Base


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text('false'))


class Vacancy(Base):
    __tablename__ = 'vacancies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    salary: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text('false'))


class LoyaltyPage(Base):
    __tablename__ = 'loyalty_page'
    __table_args__ = (CheckConstraint('id = 1', name='ck_loyalty_single_page'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(String(300), nullable=False, default='')
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text('false'))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
