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
        """Проверяет данные, назначает ID средствами БД и создаёт карточку."""

        name = full_name.strip()
        Employee.validate_full_name(name)
        inn = Employee.validate_inn(inn.strip())
        Employee.validate_dates(hire_date)
        Employee.validate_experience_years(experience_years)
        self._check_inn_unique(inn)
        tariff = self._organization.get_position(position)
        rate = self._organization.rate_for(tariff.name, experience_years)
        return self._repository.save(
            Employee(0, name, inn, tariff.name, hire_date, experience_years, rate)
        )

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
        name = full_name.strip()
        Employee.validate_full_name(name)
        inn = Employee.validate_inn(inn.strip())
        Employee.validate_dates(hire_date, old.dismissal_date)
        Employee.validate_experience_years(experience_years)
        self._check_inn_unique(inn, exclude_id=employee_id)
        tariff = self._organization.get_position(position)
        rate = self._organization.rate_for(tariff.name, experience_years)
        updated = replace(
            old,
            full_name=name,
            inn=inn,
            position=tariff.name,
            hire_date=hire_date,
            experience_years=experience_years,
            rate_per_shift=rate,
        )
        return self._repository.save(updated)

    def dismiss(self, employee_id: int, dismissal_date: date) -> Employee:
        """Устанавливает дату увольнения, не удаляя карточку."""

        old = self._repository.get(employee_id)
        if old.dismissal_date is not None:
            raise ValueError("сотрудник уже уволен")
        Employee.validate_dates(old.hire_date, dismissal_date)
        return self._repository.save(replace(old, dismissal_date=dismissal_date))

    def get(self, employee_id: int) -> Employee:
        """Возвращает карточку сотрудника."""

        return self._repository.get(employee_id)

    def list_all(self) -> list[Employee]:
        """Возвращает все карточки сотрудников."""

        return self._repository.list_all()

    def employed_in(self, period: Period) -> list[Employee]:
        """Возвращает тех, кто работал хотя бы один день в месяце."""

        staff = [
            item
            for item in self._repository.list_all()
            if item.hire_date <= period.end
            and (item.dismissal_date is None or item.dismissal_date >= period.start)
        ]
        return sorted(staff, key=lambda item: item.employee_id)

    def _check_inn_unique(self, inn: str, exclude_id: int | None = None) -> None:
        """Проверяет ИНН на повтор; свой текущий ИНН не считается повтором."""

        existing = self._repository.find_by_inn(inn)
        if existing is not None and existing.employee_id != exclude_id:
            raise ValueError("сотрудник с таким ИНН уже существует")
