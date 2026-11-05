"""Единая точка входа, содержащая только сборку приложения."""

from collections.abc import Callable

from salary_calculator.cli import SalaryCalculatorCLI
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.repositories.employee import InMemoryEmployeeRepository
from salary_calculator.repositories.statement import InMemoryStatementRepository
from salary_calculator.repositories.timesheet import InMemoryTimesheetRepository
from salary_calculator.services.auth import AuthService
from salary_calculator.services.calendar import CalendarService
from salary_calculator.services.employee import EmployeeService
from salary_calculator.services.organization import OrganizationService
from salary_calculator.services.payroll import PayrollService
from salary_calculator.services.timesheet import TimesheetService


def create_application(
    reader: InputReader | None = None,
    output: Callable[[str], None] | None = None,
) -> SalaryCalculatorCLI:
    """Соединяет InMemory-хранилища, сервисы и консольный интерфейс."""

    organization = OrganizationService()
    employees = EmployeeService(InMemoryEmployeeRepository(), organization)
    calendar = CalendarService()
    timesheets = TimesheetService(InMemoryTimesheetRepository(), employees, calendar)
    payroll = PayrollService(
        InMemoryStatementRepository(), timesheets, employees, organization
    )
    return SalaryCalculatorCLI(
        AuthService(),
        organization,
        employees,
        calendar,
        timesheets,
        payroll,
        reader,
        output,
    )


def main() -> None:
    """Запускает приложение."""

    create_application().run()


if __name__ == "__main__":
    main()
