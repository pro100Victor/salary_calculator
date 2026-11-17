"""Набор сервисов одной пользовательской операции."""

from dataclasses import dataclass

from salary_calculator.services.calendar import CalendarService
from salary_calculator.services.employee import EmployeeService
from salary_calculator.services.organization import OrganizationService
from salary_calculator.services.payroll import PayrollService
from salary_calculator.services.timesheet import TimesheetService


@dataclass(frozen=True)
class ApplicationServices:
    """Передаёт готовые сервисы интерфейсу без доступа к репозиториям."""

    organization: OrganizationService
    employees: EmployeeService
    calendar: CalendarService
    timesheets: TimesheetService
    payroll: PayrollService
