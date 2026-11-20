"""ORM-модель StatementResultRow."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from payroll.db.base import Base

if TYPE_CHECKING:
    from .employee import EmployeeRow
    from .statement import StatementRow


class StatementResultRow(Base):
    """Строка ведомости: полный снимок сотрудника на момент расчёта."""

    __tablename__ = "statement_results"
    __table_args__ = (
        CheckConstraint(
            "amount_to_pay = accrued - tax", name="statement_results_amount_balance"
        ),
        CheckConstraint("tax <= accrued", name="statement_results_tax_limit"),
        CheckConstraint(
            "worked_shifts >= 0", name="statement_results_worked_shifts_non_negative"
        ),
        CheckConstraint(
            "sick_days >= 0", name="statement_results_sick_days_non_negative"
        ),
        CheckConstraint(
            "vacation_days >= 0", name="statement_results_vacation_days_non_negative"
        ),
        CheckConstraint("accrued >= 0", name="statement_results_accrued_non_negative"),
        CheckConstraint("tax >= 0", name="statement_results_tax_non_negative"),
        CheckConstraint(
            "amount_to_pay >= 0", name="statement_results_amount_to_pay_non_negative"
        ),
    )

    statement_id: Mapped[int] = mapped_column(
        ForeignKey("statements.statement_id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="RESTRICT"), primary_key=True
    )
    # Снимок кадровой карточки на момент расчёта:
    full_name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12))
    position: Mapped[str] = mapped_column(String(120))
    hire_date: Mapped[date] = mapped_column(Date)
    experience_years: Mapped[int] = mapped_column(SmallInteger)
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Дни и суммы:
    worked_shifts: Mapped[int] = mapped_column(SmallInteger)
    sick_days: Mapped[int] = mapped_column(SmallInteger)
    vacation_days: Mapped[int] = mapped_column(SmallInteger)
    accrued: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    amount_to_pay: Mapped[Decimal] = mapped_column(Numeric(20, 2))

    statement: Mapped["StatementRow"] = relationship(back_populates="results")
    employee: Mapped["EmployeeRow"] = relationship(back_populates="results")
