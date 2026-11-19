"""Таблицы PostgreSQL, соответствующие доменным моделям проекта.

Слой не заменяет доменные dataclass-модели, а отражает их: типы колонок,
PK/FK, UNIQUE и CHECK повторяют правила моделей. Числа с плавающей точкой
не используются: деньги и проценты хранятся как Numeric.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from salary_calculator.db.base import Base


class OrganizationRow(Base):
    """Реквизиты предприятия; в таблице всегда одна строка с id = 1."""

    __tablename__ = "organization"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 255", name="organization_name_length"),
        CheckConstraint("inn ~ '^[0-9]{10}$' OR inn ~ '^[0-9]{12}$'", name="organization_inn_format"),
        CheckConstraint("kpp IS NULL OR kpp ~ '^[0-9]{9}$'", name="organization_kpp_format"),
        CheckConstraint("char_length(address) BETWEEN 1 AND 255", name="organization_address_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12))
    kpp: Mapped[str | None] = mapped_column(String(9))
    address: Mapped[str] = mapped_column(String(255))


class PositionRow(Base):
    """Должность с базовой ставкой и надбавкой за полный год стажа."""

    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 120", name="positions_name_length"),
        CheckConstraint("base_rate > 0", name="positions_base_rate_positive"),
        CheckConstraint("seniority_percent BETWEEN 0 AND 100", name="positions_seniority_percent_range"),
    )

    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    seniority_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))


class EmployeeRow(Base):
    """Кадровая карточка сотрудника."""

    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("char_length(full_name) BETWEEN 1 AND 255", name="employees_full_name_length"),
        CheckConstraint("inn ~ '^[0-9]{12}$'", name="employees_inn_format"),
        CheckConstraint("experience_years BETWEEN 0 AND 80", name="employees_experience_years_range"),
        CheckConstraint("rate_per_shift > 0", name="employees_rate_per_shift_positive"),
        CheckConstraint("dismissal_date IS NULL OR dismissal_date >= hire_date", name="employees_dates_order"),
    )

    employee_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    position: Mapped[str] = mapped_column(
        ForeignKey("positions.name", ondelete="RESTRICT"), nullable=False
    )
    hire_date: Mapped[date] = mapped_column(Date)
    experience_years: Mapped[int] = mapped_column(SmallInteger)
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class CalendarNormRow(Base):
    """Ручная норма смен на один расчётный период."""

    __tablename__ = "calendar_norms"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_calendar_norms_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="calendar_norms_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="calendar_norms_month_range"),
        CheckConstraint("shifts BETWEEN 1 AND 31", name="calendar_norms_shifts_range"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    shifts: Mapped[int] = mapped_column(SmallInteger)


class TimesheetRow(Base):
    """Шапка месячного табеля; уникальность периода гарантирует БД."""

    __tablename__ = "timesheets"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_timesheets_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="timesheets_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="timesheets_month_range"),
        CheckConstraint("shift_norm BETWEEN 1 AND 31", name="timesheets_shift_norm_range"),
        CheckConstraint("revision >= 0", name="timesheets_revision_non_negative"),
    )

    timesheet_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    shift_norm: Mapped[int] = mapped_column(SmallInteger)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    closed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class TimesheetEntryRow(Base):
    """Строка табеля одного участника; незаполненная строка — три NULL."""

    __tablename__ = "timesheet_rows"
    __table_args__ = (
        CheckConstraint("worked_shifts >= 0", name="timesheet_rows_worked_shifts_non_negative"),
        CheckConstraint("sick_days >= 0", name="timesheet_rows_sick_days_non_negative"),
        CheckConstraint("vacation_days >= 0", name="timesheet_rows_vacation_days_non_negative"),
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


class StatementRow(Base):
    """Шапка расчётной ведомости; название организации — снимок."""

    __tablename__ = "statements"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_statements_year_month"),
        CheckConstraint("year BETWEEN 1 AND 9999", name="statements_year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="statements_month_range"),
        CheckConstraint("char_length(organization_name) BETWEEN 1 AND 255", name="statements_organization_name_length"),
        CheckConstraint("source_revision >= 0", name="statements_source_revision_non_negative"),
    )

    statement_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger)
    month: Mapped[int] = mapped_column(SmallInteger)
    organization_name: Mapped[str] = mapped_column(String(255))
    source_revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class StatementResultRow(Base):
    """Строка ведомости: полный снимок сотрудника на момент расчёта."""

    __tablename__ = "statement_results"
    __table_args__ = (
        CheckConstraint("worked_shifts >= 0", name="statement_results_worked_shifts_non_negative"),
        CheckConstraint("sick_days >= 0", name="statement_results_sick_days_non_negative"),
        CheckConstraint("vacation_days >= 0", name="statement_results_vacation_days_non_negative"),
        CheckConstraint("accrued >= 0", name="statement_results_accrued_non_negative"),
        CheckConstraint("tax >= 0", name="statement_results_tax_non_negative"),
        CheckConstraint("amount_to_pay >= 0", name="statement_results_amount_to_pay_non_negative"),
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
    rate_per_shift: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    dismissal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Дни и суммы:
    worked_shifts: Mapped[int] = mapped_column(SmallInteger)
    sick_days: Mapped[int] = mapped_column(SmallInteger)
    vacation_days: Mapped[int] = mapped_column(SmallInteger)
    accrued: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_to_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2))
