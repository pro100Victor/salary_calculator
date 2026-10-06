"""Кадровые операции с проверкой данных и расчётом ставки."""

from dataclasses import replace
from datetime import date

from salary_calculator.contracts import EmployeeRepository
from salary_calculator.models import Employee, Period
from salary_calculator.organization_service import OrganizationService


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
        if old.dismissal_date is not None and hire_date > old.dismissal_date:
            raise ValueError("дата приёма не может быть позже даты увольнения")
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
        if not isinstance(dismissal_date, date):
            raise ValueError("введите корректную дату увольнения")
        if dismissal_date < employee.hire_date:
            raise ValueError("увольнение не может быть раньше приёма на работу")
        if employee.dismissal_date is not None:
            raise ValueError("сотрудник уже уволен")
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

        if not name:
            raise ValueError("ФИО не должно быть пустым")
        if len(inn) != 12 or not inn.isascii() or not inn.isdigit():
            raise ValueError("ИНН сотрудника должен содержать 12 цифр")
        if not isinstance(hire_date, date):
            raise ValueError("введите корректную дату приёма")

    def _check_inn_unique(self, inn: str, except_id: int | None = None) -> None:
        """Отклоняет дубликат ИНН среди кадровых карточек."""

        for item in self.get_all_employees():
            if item.inn == inn and item.employee_id != except_id:
                raise ValueError("сотрудник с таким ИНН уже существует")
