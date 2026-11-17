"""ORM-модель payroll_statement."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salary_calculator.db.base import Base

if TYPE_CHECKING:
    from .payroll_result import PayrollResultRow
    from .timesheet import TimesheetRow


class PayrollStatementRow(Base):
    """Сохранённая ведомость с названием организации на момент расчёта."""

    __tablename__ = "payroll_statements"
    __table_args__ = (
        CheckConstraint("source_revision >= 0", name="revision_nonnegative"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timesheet_id: Mapped[int] = mapped_column(
        ForeignKey("timesheets.id", ondelete="RESTRICT"), unique=True
    )
    organization_name: Mapped[str] = mapped_column(Text)
    source_revision: Mapped[int] = mapped_column(Integer)
    timesheet: Mapped[TimesheetRow] = relationship(back_populates="statement")
    results: Mapped[list[PayrollResultRow]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PayrollResultRow.employee_id",
    )
