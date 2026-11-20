"""Начальная схема БД Salary Calculator

Revision ID: b3d7f9a1c5e2
Revises:
Create Date: 2026-11-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d7f9a1c5e2"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("seniority_percent", sa.Numeric(5, 2), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_positions")),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 120", name=op.f("ck_positions_name_length")
        ),
        sa.CheckConstraint(
            "base_rate > 0", name=op.f("ck_positions_base_rate_positive")
        ),
        sa.CheckConstraint(
            "seniority_percent BETWEEN 0 AND 100",
            name=op.f("ck_positions_seniority_percent_range"),
        ),
    )
    op.create_table(
        "organization",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=False),
        sa.Column("kpp", sa.String(length=9), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization")),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 255",
            name=op.f("ck_organization_name_length"),
        ),
        sa.CheckConstraint(
            "inn ~ '^[0-9]{10}$' OR inn ~ '^[0-9]{12}$'",
            name=op.f("ck_organization_inn_format"),
        ),
        sa.CheckConstraint(
            "kpp IS NULL OR kpp ~ '^[0-9]{9}$'", name=op.f("ck_organization_kpp_format")
        ),
        sa.CheckConstraint(
            "char_length(address) BETWEEN 1 AND 255",
            name=op.f("ck_organization_address_length"),
        ),
    )
    op.create_table(
        "employees",
        sa.Column("employee_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("experience_years", sa.SmallInteger(), nullable=False),
        sa.Column("rate_per_shift", sa.Numeric(12, 2), nullable=False),
        sa.Column("dismissal_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["position"],
            ["positions.name"],
            name=op.f("fk_employees_position_positions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("employee_id", name=op.f("pk_employees")),
        sa.UniqueConstraint("inn", name=op.f("uq_employees_inn")),
        sa.CheckConstraint(
            "char_length(full_name) BETWEEN 1 AND 255",
            name=op.f("ck_employees_full_name_length"),
        ),
        sa.CheckConstraint("inn ~ '^[0-9]{12}$'", name=op.f("ck_employees_inn_format")),
        sa.CheckConstraint(
            "experience_years BETWEEN 0 AND 80",
            name=op.f("ck_employees_experience_years_range"),
        ),
        sa.CheckConstraint(
            "rate_per_shift > 0", name=op.f("ck_employees_rate_per_shift_positive")
        ),
        sa.CheckConstraint(
            "dismissal_date IS NULL OR dismissal_date >= hire_date",
            name=op.f("ck_employees_dates_order"),
        ),
    )
    op.create_table(
        "calendar_norms",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("shifts", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calendar_norms")),
        sa.UniqueConstraint("year", "month", name=op.f("uq_calendar_norms_year_month")),
        sa.CheckConstraint(
            "year BETWEEN 1 AND 9999", name=op.f("ck_calendar_norms_year_range")
        ),
        sa.CheckConstraint(
            "month BETWEEN 1 AND 12", name=op.f("ck_calendar_norms_month_range")
        ),
        sa.CheckConstraint(
            "shifts BETWEEN 1 AND 31", name=op.f("ck_calendar_norms_shifts_range")
        ),
    )
    op.create_table(
        "timesheets",
        sa.Column("timesheet_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("shift_norm", sa.SmallInteger(), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="0", nullable=False),
        sa.Column("closed", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("timesheet_id", name=op.f("pk_timesheets")),
        sa.UniqueConstraint("year", "month", name=op.f("uq_timesheets_year_month")),
        sa.CheckConstraint(
            "year BETWEEN 1 AND 9999", name=op.f("ck_timesheets_year_range")
        ),
        sa.CheckConstraint(
            "month BETWEEN 1 AND 12", name=op.f("ck_timesheets_month_range")
        ),
        sa.CheckConstraint(
            "shift_norm BETWEEN 1 AND 31", name=op.f("ck_timesheets_shift_norm_range")
        ),
        sa.CheckConstraint(
            "revision >= 0", name=op.f("ck_timesheets_revision_non_negative")
        ),
    )
    op.create_table(
        "timesheet_rows",
        sa.Column("timesheet_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("worked_shifts", sa.SmallInteger(), nullable=True),
        sa.Column("sick_days", sa.SmallInteger(), nullable=True),
        sa.Column("vacation_days", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["timesheet_id"],
            ["timesheets.timesheet_id"],
            name=op.f("fk_timesheet_rows_timesheet_id_timesheets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.employee_id"],
            name=op.f("fk_timesheet_rows_employee_id_employees"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "timesheet_id", "employee_id", name=op.f("pk_timesheet_rows")
        ),
        sa.CheckConstraint(
            "worked_shifts >= 0",
            name=op.f("ck_timesheet_rows_worked_shifts_non_negative"),
        ),
        sa.CheckConstraint(
            "sick_days >= 0", name=op.f("ck_timesheet_rows_sick_days_non_negative")
        ),
        sa.CheckConstraint(
            "vacation_days >= 0",
            name=op.f("ck_timesheet_rows_vacation_days_non_negative"),
        ),
        sa.CheckConstraint(
            "(worked_shifts IS NULL AND sick_days IS NULL AND vacation_days IS NULL) "
            "OR (worked_shifts IS NOT NULL AND sick_days IS NOT NULL AND vacation_days IS NOT NULL)",
            name=op.f("ck_timesheet_rows_all_or_nothing"),
        ),
    )
    op.create_table(
        "statements",
        sa.Column("statement_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("source_revision", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("statement_id", name=op.f("pk_statements")),
        sa.UniqueConstraint("year", "month", name=op.f("uq_statements_year_month")),
        sa.CheckConstraint(
            "year BETWEEN 1 AND 9999", name=op.f("ck_statements_year_range")
        ),
        sa.CheckConstraint(
            "month BETWEEN 1 AND 12", name=op.f("ck_statements_month_range")
        ),
        sa.CheckConstraint(
            "char_length(organization_name) BETWEEN 1 AND 255",
            name=op.f("ck_statements_organization_name_length"),
        ),
        sa.CheckConstraint(
            "source_revision >= 0",
            name=op.f("ck_statements_source_revision_non_negative"),
        ),
    )
    op.create_table(
        "statement_results",
        sa.Column("statement_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("experience_years", sa.SmallInteger(), nullable=False),
        sa.Column("rate_per_shift", sa.Numeric(12, 2), nullable=False),
        sa.Column("dismissal_date", sa.Date(), nullable=True),
        sa.Column("worked_shifts", sa.SmallInteger(), nullable=False),
        sa.Column("sick_days", sa.SmallInteger(), nullable=False),
        sa.Column("vacation_days", sa.SmallInteger(), nullable=False),
        sa.Column("accrued", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_to_pay", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.statement_id"],
            name=op.f("fk_statement_results_statement_id_statements"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.employee_id"],
            name=op.f("fk_statement_results_employee_id_employees"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "statement_id", "employee_id", name=op.f("pk_statement_results")
        ),
        sa.CheckConstraint(
            "worked_shifts >= 0",
            name=op.f("ck_statement_results_worked_shifts_non_negative"),
        ),
        sa.CheckConstraint(
            "sick_days >= 0", name=op.f("ck_statement_results_sick_days_non_negative")
        ),
        sa.CheckConstraint(
            "vacation_days >= 0",
            name=op.f("ck_statement_results_vacation_days_non_negative"),
        ),
        sa.CheckConstraint(
            "accrued >= 0", name=op.f("ck_statement_results_accrued_non_negative")
        ),
        sa.CheckConstraint(
            "tax >= 0", name=op.f("ck_statement_results_tax_non_negative")
        ),
        sa.CheckConstraint(
            "amount_to_pay >= 0",
            name=op.f("ck_statement_results_amount_to_pay_non_negative"),
        ),
    )


def downgrade() -> None:
    op.drop_table("statement_results")
    op.drop_table("statements")
    op.drop_table("timesheet_rows")
    op.drop_table("timesheets")
    op.drop_table("calendar_norms")
    op.drop_table("employees")
    op.drop_table("organization")
    op.drop_table("positions")
