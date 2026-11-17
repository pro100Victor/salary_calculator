"""ORM-модель payroll_result."""

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

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .payroll_statement import PayrollStatementRow


class PayrollResultRow(Base):
    """Персональный расчёт с самостоятельным снимком кадровых полей."""

    __tablename__ = "payroll_results"
    __table_args__ = (
        UniqueConstraint("statement_id", "employee_id"),
        CheckConstraint(
            "worked_shifts >= 0 AND sick_days >= 0 AND vacation_days >= 0",
            name="days_nonnegative",
        ),
        CheckConstraint(
            "accrued >= 0 AND tax >= 0 AND amount_to_pay >= 0",
            name="amounts_nonnegative",
        ),
        CheckConstraint("amount_to_pay = accrued - tax", name="amount_balance"),
        CheckConstraint(
            "experience_years BETWEEN 0 AND 80 AND rate_per_shift > 0",
            name="snapshot_range",
        ),
        CheckConstraint(
            "dismissal_date IS NULL OR dismissal_date >= hire_date",
            name="snapshot_dates",
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_statements.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    full_name: Mapped[str] = mapped_column(Text)
    inn: Mapped[str] = mapped_column(Text)
    position_name: Mapped[str] = mapped_column(Text)
    hire_date: Mapped[date] = mapped_column(Date)
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer)
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    worked_shifts: Mapped[int] = mapped_column(Integer)
    sick_days: Mapped[int] = mapped_column(Integer)
    vacation_days: Mapped[int] = mapped_column(Integer)
    accrued: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    amount_to_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    statement: Mapped[PayrollStatementRow] = relationship(back_populates="results")
    employee: Mapped[EmployeeRow] = relationship(back_populates="results")
