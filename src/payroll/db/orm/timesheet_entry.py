"""ORM-модель TimesheetEntryRow."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payroll.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .timesheet import TimesheetRow


class TimesheetEntryRow(Base):
    """Строка табеля одного участника; незаполненная строка — три NULL."""

    __tablename__ = "timesheet_rows"
    __table_args__ = (
        CheckConstraint(
            "worked_shifts >= 0", name="timesheet_rows_worked_shifts_non_negative"
        ),
        CheckConstraint("sick_days >= 0", name="timesheet_rows_sick_days_non_negative"),
        CheckConstraint(
            "vacation_days >= 0", name="timesheet_rows_vacation_days_non_negative"
        ),
        CheckConstraint(
            "(worked_shifts IS NULL AND sick_days IS NULL AND vacation_days IS NULL) "
            "OR (worked_shifts IS NOT NULL AND sick_days IS NOT NULL AND vacation_days IS NOT NULL)",
            name="timesheet_rows_all_or_nothing",
        ),
    )

    timesheet_id: Mapped[int] = mapped_column(
        ForeignKey("timesheets.timesheet_id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="RESTRICT"), primary_key=True
    )
    worked_shifts: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sick_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    vacation_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    timesheet: Mapped["TimesheetRow"] = relationship(back_populates="entries")
    employee: Mapped["EmployeeRow"] = relationship(back_populates="entries")
