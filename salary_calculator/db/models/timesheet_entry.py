"""ORM-модель timesheet_entry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .timesheet import TimesheetRow


class TimesheetEntryRow(Base):
    """Связь сотрудник–табель; NULL во всех трёх полях означает незаполненную строку."""

    __tablename__ = "timesheet_entries"
    __table_args__ = (
        CheckConstraint(
            "(worked_shifts IS NULL AND sick_days IS NULL AND vacation_days IS NULL) OR (worked_shifts IS NOT NULL AND sick_days IS NOT NULL AND vacation_days IS NOT NULL AND worked_shifts >= 0 AND sick_days >= 0 AND vacation_days >= 0)",
            name="entry_state",
        ),
    )
    timesheet_id: Mapped[int] = mapped_column(
        ForeignKey("timesheets.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), primary_key=True
    )
    worked_shifts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sick_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vacation_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timesheet: Mapped[TimesheetRow] = relationship(back_populates="rows")
    employee: Mapped[EmployeeRow] = relationship(back_populates="timesheet_rows")
