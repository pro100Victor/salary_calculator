"""Представления состояния для экранов; чтение не создаёт табели."""

from typing import Any

from payroll.application.services import ApplicationServices
from payroll.models import Period
from payroll.web.serialization import to_json


def directory_view(services: ApplicationServices) -> dict[str, Any]:
    """Возвращает реквизиты, должности и сотрудников с серверными ставками."""

    try:
        organization = services.organization.get_organization()
    except LookupError:
        organization = None
    employees = [
        {**to_json(item), "status": item.status}
        for item in services.employees.get_all_employees()
    ]
    return {
        "organization": to_json(organization),
        "positions": to_json(services.organization.list_positions()),
        "employees": employees,
    }


def period_view(services: ApplicationServices, period: Period) -> dict[str, Any]:
    """Возвращает табель и ведомость с итогами и признаком устаревания."""

    try:
        timesheet = services.timesheets.get(period)
    except LookupError:
        timesheet = None
    try:
        statement = services.payroll.get_statement(period)
    except LookupError:
        statement = None
    statement_data = None
    if statement is not None:
        statement_data = {
            **to_json(statement),
            "total_accrued": str(statement.total_accrued),
            "total_tax": str(statement.total_tax),
            "total_to_pay": str(statement.total_to_pay),
            "is_current": services.payroll.is_current(period),
        }
    return {
        "period": to_json(period),
        "norm": timesheet.shift_norm
        if timesheet
        else services.calendar.get_norm(period),
        "timesheet": to_json(timesheet),
        "statement": statement_data,
    }
