"""Перевод ORM-рядов в доменные dataclass-модели и обратно."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

from salary_calculator.db.models import (
    EmployeeRow,
    OrganizationRow,
    PositionRow,
    StatementResultRow,
    StatementRow,
    TimesheetEntryRow,
    TimesheetRow,
)
from salary_calculator.models import (
    Employee,
    Organization,
    PayrollResult,
    PayrollStatement,
    Period,
    Position,
    Timesheet,
    TimesheetEntry,
)


def organization_to_domain(row: OrganizationRow) -> Organization:
    """Собирает доменную модель реквизитов из ORM-ряда."""

    return Organization(row.name, row.inn, row.kpp or "", row.address)


def apply_organization(row: OrganizationRow, organization: Organization) -> None:
    """Переносит доменные реквизиты в ORM-ряд (КПП-пустота это NULL)."""

    row.name = organization.name
    row.inn = organization.inn
    row.kpp = organization.kpp or None
    row.address = organization.address


def position_to_domain(row: PositionRow) -> Position:
    """Собирает доменную модель должности из ORM-ряда."""

    return Position(row.name, row.base_rate, row.seniority_percent)


def employee_to_domain(row: EmployeeRow) -> Employee:
    """Собирает кадровую карточку из ORM-ряда."""

    return Employee(
        row.employee_id,
        row.full_name,
        row.inn,
        row.position,
        row.hire_date,
        row.experience_years,
        row.rate_per_shift,
        row.dismissal_date,
    )


def employee_fields(employee: Employee) -> dict[str, object]:
    """Возвращает изменяемые поля карточки для записи в ORM-ряд."""

    return {
        "full_name": employee.full_name,
        "inn": employee.inn,
        "position": employee.position,
        "hire_date": employee.hire_date,
        "experience_years": employee.experience_years,
        "rate_per_shift": employee.rate_per_shift,
        "dismissal_date": employee.dismissal_date,
    }


def timesheet_to_domain(header: TimesheetRow, rows: list[TimesheetEntryRow]) -> Timesheet:
    """Собирает доменный табель: участники из всех строк, записи из заполненных."""

    entries = {
        row.employee_id: TimesheetEntry(
            row.employee_id, row.worked_shifts, row.sick_days, row.vacation_days
        )
        for row in rows
        if row.worked_shifts is not None
    }
    return Timesheet(
        Period(header.year, header.month),
        header.shift_norm,
        tuple(row.employee_id for row in rows),
        entries,
        header.revision,
        header.closed,
    )


def statement_to_domain(
    header: StatementRow, rows: list[StatementResultRow]
) -> PayrollStatement:
    """Собирает ведомость со снимками сотрудников из строк результата."""

    results = []
    for row in rows:
        snapshot = Employee(
            row.employee_id,
            row.full_name,
            row.inn,
            row.position,
            row.hire_date,
            row.experience_years,
            row.rate_per_shift,
            row.dismissal_date,
        )
        results.append(
            PayrollResult(
                snapshot,
                row.worked_shifts,
                row.sick_days,
                row.vacation_days,
                row.accrued,
                row.tax,
                row.amount_to_pay,
            )
        )
    return PayrollStatement(
        Period(header.year, header.month),
        header.organization_name,
        tuple(results),
        header.source_revision,
    )


def result_fields(result: PayrollResult) -> dict[str, object]:
    """Возвращает поля строки ведомости для записи в ORM-ряд."""

    return {
        "full_name": result.employee.full_name,
        "inn": result.employee.inn,
        "position": result.employee.position,
        "hire_date": result.employee.hire_date,
        "experience_years": result.employee.experience_years,
        "rate_per_shift": result.employee.rate_per_shift,
        "dismissal_date": result.employee.dismissal_date,
        "worked_shifts": result.worked_shifts,
        "sick_days": result.sick_days,
        "vacation_days": result.vacation_days,
        "accrued": result.accrued,
        "tax": result.tax,
        "amount_to_pay": result.amount_to_pay,
    }
