"""Кадровые операции с проверкой данных и расчётом ставки."""

from dataclasses import replace
from datetime import date

from salary_calculator.models import Employee, Period
from salary_calculator.repositories.employee import EmployeeRepository
from salary_calculator.services.organization import OrganizationService


class EmployeeService:
    """Управляет карточками сотрудников через абстрактное хранилище."""

    def __init__(
        self, repository: EmployeeRepository, organization: OrganizationService
    ) -> None:
        """Получает InMemory-хранилище и тарифы организации."""

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
        """Проверяет данные, назначает ID и создаёт кадровую карточку."""

        name, inn = full_name.strip(), inn.strip()
        self._validate(name, inn, hire_date)
        self._check_inn_unique(inn)
        rate = self._organization.rate_for(position, experience_years)
        employees = self._repository.list_all()
        next_id = max((item.employee_id for item in employees), default=0) + 1
        employee = Employee(
            next_id,
            name,
            inn,
            self._organization.get_position(position).name,
            hire_date,
            experience_years,
            rate,
        )
        self._repository.save(employee)
        return employee

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
        self._validate(name, inn, hire_date)
        self._check_inn_unique(inn, except_id=employee_id)
        rate = self._organization.rate_for(position, experience_years)
        self.validate_hire_date(hire_date, old.dismissal_date)
        updated = replace(
            old,
            full_name=name,
            inn=inn,
            position=self._organization.get_position(position).name,
            hire_date=hire_date,
            experience_years=experience_years,
            rate_per_shift=rate,
        )
        self._repository.save(updated)
        return updated

    def dismiss_employee(self, employee_id: int, dismissal_date: date) -> Employee:
        """Устанавливает дату увольнения без удаления истории сотрудника."""

        employee = self._repository.get(employee_id)
        self.validate_dismissal_date(employee_id, dismissal_date)
        updated = replace(employee, dismissal_date=dismissal_date)
        self._repository.save(updated)
        return updated

    def get_employee_by_id(self, employee_id: int) -> Employee:
        """Возвращает сотрудника по идентификатору."""

        return self._repository.get(employee_id)

    def get_all_employees(self) -> list[Employee]:
        """Возвращает все кадровые карточки, включая уволенных."""

        return self._repository.list_all()

    def employed_in(self, period: Period) -> list[Employee]:
        """Отбирает сотрудников, работавших в расчётном месяце."""

        return [item for item in self.get_all_employees() if item.employed_in(period)]

    def _validate(self, name: str, inn: str, hire_date: date) -> None:
        """Проверяет обязательные кадровые сведения."""

        self.validate_full_name(name)

        Employee.validate_inn(inn)

        self.validate_hire_date(hire_date)

    def validate_inn(self, value: str, except_id: int | None = None) -> None:
        """Проверяет формат и уникальность ИНН без сохранения карточки."""

        Employee.validate_inn(value)
        self._check_inn_unique(value, except_id=except_id)

    def _check_inn_unique(self, inn: str, except_id: int | None = None) -> None:
        """Отклоняет дубликат ИНН среди кадровых карточек."""

        for item in self.get_all_employees():
            if item.inn == inn and item.employee_id != except_id:
                raise ValueError("сотрудник с таким ИНН уже существует")

    @staticmethod
    def validate_full_name(value: str) -> None:
        """Проверяет ФИО сотрудника."""
        if not value.strip():
            raise ValueError("ФИО не должно быть пустым")

    @staticmethod
    def validate_hire_date(value: date, dismissal_date: date | None = None) -> None:
        """Проверяет дату приёма."""
        if not isinstance(value, date):
            raise ValueError("введите корректную дату приёма")
        if dismissal_date is not None and value > dismissal_date:
            raise ValueError("дата приёма не может быть позже даты увольнения")

    def validate_dismissal_date(self, employee_id: int, dismissal_date: date) -> None:
        """Проверяет дату увольнения без изменения карточки."""
        employee = self.get_employee_by_id(employee_id)
        if not isinstance(dismissal_date, date):
            raise ValueError("введите корректную дату увольнения")
        if dismissal_date < employee.hire_date:
            raise ValueError("увольнение не может быть раньше приёма на работу")
        if employee.dismissal_date is not None:
            raise ValueError("сотрудник уже уволен")
