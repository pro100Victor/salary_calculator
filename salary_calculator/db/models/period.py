"""ORM-модель period."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .organization import OrganizationRow
    from .timesheet import TimesheetRow


class PeriodRow(Base):
    """Месяц расчёта с необязательной ручной нормой до создания табеля."""

    __tablename__ = "periods"
    __table_args__ = (
        UniqueConstraint("organization_id", "year", "month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),
        CheckConstraint(
            "norm_override IS NULL OR norm_override BETWEEN 1 AND 31", name="norm_range"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), default=1
    )
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    norm_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    organization: Mapped[OrganizationRow] = relationship(back_populates="periods")
    timesheet: Mapped[TimesheetRow | None] = relationship(
        back_populates="period", passive_deletes="all"
    )
