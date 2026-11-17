"""ORM-модель timesheet."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .payroll_statement import PayrollStatementRow
    from .period import PeriodRow
    from .timesheet_entry import TimesheetEntryRow


class TimesheetRow(Base):
    """Зафиксированные состав, норма, версия и статус табеля."""

    __tablename__ = "timesheets"
    __table_args__ = (
        CheckConstraint("shift_norm BETWEEN 1 AND 31", name="norm_range"),
        CheckConstraint("revision >= 0", name="revision_nonnegative"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_id: Mapped[int] = mapped_column(
        ForeignKey("periods.id", ondelete="RESTRICT"), unique=True
    )
    shift_norm: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    period: Mapped[PeriodRow] = relationship(back_populates="timesheet")
    rows: Mapped[list[TimesheetEntryRow]] = relationship(
        back_populates="timesheet",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TimesheetEntryRow.employee_id",
    )
    employees: Mapped[list[EmployeeRow]] = relationship(
        secondary="timesheet_entries", back_populates="timesheets", viewonly=True
    )
    statement: Mapped[PayrollStatementRow | None] = relationship(
        back_populates="timesheet", passive_deletes="all"
    )
