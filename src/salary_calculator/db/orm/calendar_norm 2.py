"""ORM-модель CalendarNormRow."""

from salary_calculator.db.base import Base
from sqlalchemy import (
    CheckConstraint,
    Identity,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


class CalendarNormRow(Base):
    """Ручная норма смен на один расчётный период."""

    __tablename__ = "calendar_norms"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_calendar_norms_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="calendar_norms_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="calendar_norms_month_range"),
        CheckConstraint("shifts BETWEEN 1 AND 31", name="calendar_norms_shifts_range"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    shifts: Mapped[int] = mapped_column(SmallInteger)
