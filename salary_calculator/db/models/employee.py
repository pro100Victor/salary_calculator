"""ORM-модель employee."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base
from salary_calculator.db.checks import digits_only

if TYPE_CHECKING:
    from .organization import OrganizationRow
    from .payroll_result import PayrollResultRow
    from .position import PositionRow
    from .timesheet import TimesheetRow
    from .timesheet_entry import TimesheetEntryRow


class EmployeeRow(Base):
    """Живая кадровая карточка; увольнение сохраняет историю."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("organization_id", "inn"),
        CheckConstraint("length(trim(full_name)) > 0", name="name_required"),
        CheckConstraint(
            "length(inn) = 12 AND " + digits_only("inn"), name="inn_format"
        ),
        CheckConstraint("experience_years BETWEEN 0 AND 80", name="experience_range"),
        CheckConstraint("rate_per_shift > 0", name="rate_positive"),
        CheckConstraint(
            "dismissal_date IS NULL OR dismissal_date >= hire_date", name="date_order"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), default=1
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="RESTRICT"), index=True
    )
    full_name: Mapped[str] = mapped_column(Text)
    inn: Mapped[str] = mapped_column(Text)
    hire_date: Mapped[date] = mapped_column(Date)
    experience_years: Mapped[int] = mapped_column(Integer)
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    organization: Mapped[OrganizationRow] = relationship(back_populates="employees")
    position: Mapped[PositionRow] = relationship(back_populates="employees")
    timesheet_rows: Mapped[list[TimesheetEntryRow]] = relationship(
        back_populates="employee", passive_deletes="all"
    )
    timesheets: Mapped[list[TimesheetRow]] = relationship(
        secondary="timesheet_entries", back_populates="employees", viewonly=True
    )
    results: Mapped[list[PayrollResultRow]] = relationship(
        back_populates="employee", passive_deletes="all"
    )
