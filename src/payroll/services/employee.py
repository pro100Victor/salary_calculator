"""Кадровые операции с проверкой данных и расчётом ставки."""

from dataclasses import replace
from datetime import date

from payroll.models import Employee, Period
from payroll.repositories.employee import EmployeeRepository
from payroll.services.organization import OrganizationService


class EmployeeService:
    """Управляет карточками сотрудников через абстрактное хранилище."""

    def __init__(
        self, repository: EmployeeRepository, organization: OrganizationService
    ) -> None:
        """Получает хранилище сотрудников и тарифы организации."""

        self._repository = repository
        self._organization = organization

    def add_employee(
        self,
        full_name: str,
        inn: str,
        position: str,
        hire_date: date,
        experience_years: int,
    ) -> Employee:
        """Проверяет данные и создаёт карточку с ID, назначенным хранилищем."""

        name, inn = full_name.strip(), inn.strip()
        self._validate(name, inn, hire_date)
        self._check_inn_unique(inn)
        rate = self._organization.rate_for(position, experience_years)
        employee = Employee(
            0,
            name,
            inn,
            self._organization.get_position(position).name,
            hire_date,
            experience_years,
            rate,
        )
        return self._repository.save(employee)

    def update_employee(
        self,
        employee_id: int,
        full_name: str,
        inn: str,
        position: str,
        hire_date: date,
        experience_years: int,
    ) -> Employee:
        """Изменяет карточку сотрудника и пересчитывает его ставку."""

        old = self._repository.get(employee_id)
        name, inn = full_name.strip(), inn.strip()
        self._validate(name, inn, hire_date, old.dismissal_date)
        self._check_inn_unique(inn, except_id=employee_id)
        rate = self._organization.rate_for(position, experience_years)
        updated = replace(
            old,
            full_name=name,
            inn=inn,
            position=self._organization.get_position(position).name,
            hire_date=hire_date,
            experience_years=experience_years,
            rate_per_shift=rate,
        )
        return self._repository.save(updated)

    def dismiss_employee(self, employee_id: int, dismissal_date: date) -> Employee:
        """Сохраняет увольнение без удаления кадровой истории."""

        employee = self._repository.get(employee_id)
        self._validate_dismissal(employee, dismissal_date)
        updated = replace(employee, dismissal_date=dismissal_date)
        return self._repository.save(updated)

    def get_employee_by_id(self, employee_id: int) -> Employee:
        """Возвращает сотрудника по идентификатору."""

        return self._repository.get(employee_id)

    def get_all_employees(self) -> list[Employee]:
        """Возвращает все кадровые карточки, включая уволенных."""

        return self._repository.list_all()

    def employed_in(self, period: Period) -> list[Employee]:
        """Отбирает сотрудников, работавших в расчётном месяце."""

        return [item for item in self.get_all_employees() if item.employed_in(period)]

    def _validate(
        self,
        name: str,
        inn: str,
        hire_date: date,
        dismissal_date: date | None = None,
    ) -> None:
        """Проверяет обязательные поля и порядок дат сотрудника."""

        self.validate_full_name(name)
        Employee.validate_inn(inn)
        self.validate_hire_date(hire_date, dismissal_date)

    def validate_inn(self, value: str, except_id: int | None = None) -> None:
        """Проверяет формат и уникальность ИНН без сохранения карточки."""

        Employee.validate_inn(value)
        self._check_inn_unique(value, except_id=except_id)

    def _check_inn_unique(self, inn: str, except_id: int | None = None) -> None:
        """Отклоняет ИНН, принадлежащий другому сотруднику."""

        existing = self._repository.find_by_inn(inn)
        if existing is not None and existing.employee_id != except_id:
            raise ValueError("сотрудник с таким ИНН уже существует")

    @staticmethod
    def validate_full_name(value: str) -> None:
        """Проверяет ФИО для предварительного ввода."""
        Employee.validate_full_name(value)

    @staticmethod
    def validate_hire_date(value: date, dismissal_date: date | None = None) -> None:
        """Проверяет дату приёма для предварительного ввода."""
        Employee.validate_dates(value, dismissal_date)

    def validate_dismissal_date(self, employee_id: int, dismissal_date: date) -> None:
        """Проверяет увольнение без изменения карточки."""

        employee = self.get_employee_by_id(employee_id)
        self._validate_dismissal(employee, dismissal_date)

    @staticmethod
    def _validate_dismissal(employee: Employee, dismissal_date: date) -> None:
        """Проверяет увольнение уже полученного сотрудника."""

        Employee.validate_dates(employee.hire_date, dismissal_date)
        if employee.dismissal_date is not None:
            raise ValueError("сотрудник уже уволен")
