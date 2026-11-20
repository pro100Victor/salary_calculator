"""ORM-модель EmployeeRow."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from salary_calculator.db.base import Base
from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .position import PositionRow
    from .statement_result import StatementResultRow
    from .timesheet import TimesheetRow
    from .timesheet_entry import TimesheetEntryRow


class EmployeeRow(Base):
    """Кадровая карточка сотрудника."""

    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint(
            "char_length(trim(full_name)) BETWEEN 1 AND 255",
            name="employees_full_name_length",
        ),
        CheckConstraint("inn ~ '^[0-9]{12}$'", name="employees_inn_format"),
        CheckConstraint(
            "experience_years BETWEEN 0 AND 80", name="employees_experience_years_range"
        ),
        CheckConstraint("rate_per_shift > 0", name="employees_rate_per_shift_positive"),
        CheckConstraint(
            "dismissal_date IS NULL OR dismissal_date >= hire_date",
            name="employees_dates_order",
        ),
    )

    employee_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    position: Mapped[str] = mapped_column(
        ForeignKey("positions.name", ondelete="RESTRICT"), nullable=False
    )
    hire_date: Mapped[date] = mapped_column(Date)
    experience_years: Mapped[int] = mapped_column(SmallInteger)
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    position_row: Mapped["PositionRow"] = relationship(back_populates="employees")
    entries: Mapped[list["TimesheetEntryRow"]] = relationship(
        back_populates="employee", passive_deletes="all"
    )
    results: Mapped[list["StatementResultRow"]] = relationship(
        back_populates="employee", passive_deletes="all"
    )
    timesheets: Mapped[list["TimesheetRow"]] = relationship(
        secondary="timesheet_rows", back_populates="employees", viewonly=True
    )
