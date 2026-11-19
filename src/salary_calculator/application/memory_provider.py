"""Рабочая сборка текущего проекта без базы данных."""

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

from salary_calculator.application.provider import ServiceProvider
from salary_calculator.application.services import ApplicationServices
from salary_calculator.repositories.calendar_norm import (
    InMemoryCalendarNormRepository,
)
from salary_calculator.repositories.employee import InMemoryEmployeeRepository
from salary_calculator.repositories.organization import (
    InMemoryOrganizationRepository,
)
from salary_calculator.repositories.position import InMemoryPositionRepository
from salary_calculator.repositories.statement import InMemoryStatementRepository
from salary_calculator.repositories.timesheet import InMemoryTimesheetRepository
from salary_calculator.services.calendar import CalendarService
from salary_calculator.services.employee import EmployeeService
from salary_calculator.services.organization import OrganizationService
from salary_calculator.services.payroll import PayrollService
from salary_calculator.services.timesheet import TimesheetService


class InMemoryServiceProvider(ServiceProvider):
    """Сохраняет сервисы между запросами одного процесса и исключает гонки записи."""

    def __init__(self) -> None:
        """Собирает существующие сервисы с общей организацией и календарём."""

        organization = OrganizationService(
            InMemoryOrganizationRepository(), InMemoryPositionRepository()
        )
        employees = EmployeeService(InMemoryEmployeeRepository(), organization)
        calendar = CalendarService(InMemoryCalendarNormRepository())
        timesheets = TimesheetService(
            InMemoryTimesheetRepository(), employees, calendar
        )
        payroll = PayrollService(
            InMemoryStatementRepository(), timesheets, employees, organization
        )
        self._services = ApplicationServices(
            organization, employees, calendar, timesheets, payroll
        )
        self._lock = RLock()

    @property
    def storage_mode(self) -> str:
        """Предупреждает интерфейс об отсутствии долговременного хранения."""

        return "InMemory — данные до остановки сервера"

    @contextmanager
    def operation(self) -> Iterator[ApplicationServices]:
        """Последовательно выполняет операции; не имитирует SQL-транзакции."""

        with self._lock:
            yield self._services
