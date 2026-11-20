"""Рабочая сборка текущего проекта без базы данных."""

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

from payroll.application.provider import ServiceProvider
from payroll.application.services import ApplicationServices
from payroll.repositories.calendar_norm import (
    InMemoryCalendarNormRepository,
)
from payroll.repositories.employee import InMemoryEmployeeRepository
from payroll.repositories.organization import (
    InMemoryOrganizationRepository,
)
from payroll.repositories.position import InMemoryPositionRepository
from payroll.repositories.statement import InMemoryStatementRepository
from payroll.repositories.timesheet import InMemoryTimesheetRepository
from payroll.services.calendar import CalendarService
from payroll.services.employee import EmployeeService
from payroll.services.organization import OrganizationService
from payroll.services.payroll import PayrollService
from payroll.services.timesheet import TimesheetService


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
