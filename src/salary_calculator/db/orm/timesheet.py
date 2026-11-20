"""ORM-модель TimesheetRow."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Identity,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .statement import StatementRow
    from .timesheet_entry import TimesheetEntryRow


class TimesheetRow(Base):
    """Шапка месячного табеля; уникальность периода гарантирует БД."""

    __tablename__ = "timesheets"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_timesheets_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="timesheets_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="timesheets_month_range"),
        CheckConstraint(
            "shift_norm BETWEEN 1 AND 31", name="timesheets_shift_norm_range"
        ),
        CheckConstraint("revision >= 0", name="timesheets_revision_non_negative"),
    )

    timesheet_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    shift_norm: Mapped[int] = mapped_column(SmallInteger)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    closed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    entries: Mapped[list["TimesheetEntryRow"]] = relationship(
        back_populates="timesheet", cascade="all, delete-orphan", passive_deletes=True
    )
    employees: Mapped[list["EmployeeRow"]] = relationship(
        secondary="timesheet_rows", back_populates="timesheets", viewonly=True
    )
    statement: Mapped["StatementRow | None"] = relationship(
        back_populates="timesheet", passive_deletes="all"
    )
