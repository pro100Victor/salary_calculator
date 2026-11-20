"""Набор сервисов одной пользовательской операции."""

from dataclasses import dataclass

from payroll.services.calendar import CalendarService
from payroll.services.employee import EmployeeService
from payroll.services.organization import OrganizationService
from payroll.services.payroll import PayrollService
from payroll.services.timesheet import TimesheetService


@dataclass(frozen=True)
class ApplicationServices:
    """Передаёт готовые сервисы интерфейсу без доступа к репозиториям."""

    organization: OrganizationService
    employees: EmployeeService
    calendar: CalendarService
    timesheets: TimesheetService
    payroll: PayrollService
