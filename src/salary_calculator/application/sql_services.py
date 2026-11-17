"""Сборка предметных сервисов на одной внешней SQLAlchemy Session."""

from sqlalchemy.orm import Session

from salary_calculator.application.services import ApplicationServices
from salary_calculator.repositories.employee import SQLAlchemyEmployeeRepository
from salary_calculator.repositories.norm import SQLAlchemyNormRepository
from salary_calculator.repositories.organization import SQLAlchemyOrganizationRepository
from salary_calculator.repositories.position import SQLAlchemyPositionRepository
from salary_calculator.repositories.statement import SQLAlchemyStatementRepository
from salary_calculator.repositories.timesheet import SQLAlchemyTimesheetRepository
from salary_calculator.services.calendar import CalendarService
from salary_calculator.services.employee import EmployeeService
from salary_calculator.services.organization import OrganizationService
from salary_calculator.services.payroll import PayrollService
from salary_calculator.services.timesheet import TimesheetService


def build_sql_services(session: Session) -> ApplicationServices:
    """Не открывает транзакцию и не закрывает Session: это делает SQL-провайдер."""
    organization = OrganizationService(
        SQLAlchemyOrganizationRepository(session), SQLAlchemyPositionRepository(session)
    )
    employees = EmployeeService(SQLAlchemyEmployeeRepository(session), organization)
    calendar = CalendarService(SQLAlchemyNormRepository(session))
    timesheets = TimesheetService(
        SQLAlchemyTimesheetRepository(session), employees, calendar
    )
    payroll = PayrollService(
        SQLAlchemyStatementRepository(session), timesheets, employees, organization
    )
    return ApplicationServices(organization, employees, calendar, timesheets, payroll)
