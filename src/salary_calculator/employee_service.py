"""Сервис управления сотрудниками в оперативной памяти."""

import math

from salary_calculator.models import Employee


class EmployeeService:
    """Добавляет, хранит и возвращает сотрудников во время работы программы."""

    def __init__(self) -> None:
        """Создаёт пустое InMemory-хранилище сотрудников."""

        self._employees: list[Employee] = []
        self._next_employee_id = 1

    def add_employee(
        self,
        full_name: str,
        inn: str,
        position: str,
        rate_per_shift: float,
    ) -> Employee:
        """Проверяет данные и добавляет нового сотрудника."""

        prepared_name = full_name.strip()
        prepared_inn = inn.strip()
        prepared_position = position.strip()

        self._validate_name(prepared_name)
        self._validate_inn(prepared_inn)
        self._validate_position(prepared_position)
        self._validate_rate(rate_per_shift)
        self._check_inn_is_unique(prepared_inn)

        employee = Employee(
            employee_id=self._next_employee_id,
            full_name=prepared_name,
            inn=prepared_inn,
            position=prepared_position,
            rate_per_shift=float(rate_per_shift),
        )

        self._employees.append(employee)
        self._next_employee_id += 1
        return employee

    def get_all_employees(self) -> list[Employee]:
        """Возвращает копию списка всех сотрудников."""

        return self._employees.copy()

    def get_employee_by_id(self, employee_id: int) -> Employee:
        """Возвращает сотрудника с указанным идентификатором."""

        for employee in self._employees:
            if employee.employee_id == employee_id:
                return employee

        raise LookupError(f"сотрудник с ID {employee_id} не найден")

    def _validate_name(self, full_name: str) -> None:
        """Проверяет, что ФИО сотрудника заполнено."""

        if not full_name:
            raise ValueError("ФИО сотрудника не должно быть пустым")

    def _validate_inn(self, inn: str) -> None:
        """Проверяет российский ИНН физического лица."""

        if len(inn) != 12 or not inn.isdigit():
            raise ValueError("ИНН сотрудника должен состоять из 12 цифр")

    def _validate_position(self, position: str) -> None:
        """Проверяет, что должность сотрудника заполнена."""

        if not position:
            raise ValueError("должность сотрудника не должна быть пустой")

    def _validate_rate(self, rate_per_shift: float) -> None:
        """Проверяет корректность ставки за одну смену."""

        if isinstance(rate_per_shift, bool) or not isinstance(
            rate_per_shift,
            (int, float),
        ):
            raise ValueError("ставка за смену должна быть числом")

        if not math.isfinite(rate_per_shift) or rate_per_shift <= 0:
            raise ValueError("ставка за смену должна быть больше нуля")

    def _check_inn_is_unique(self, inn: str) -> None:
        """Проверяет отсутствие сотрудника с таким же ИНН."""

        for employee in self._employees:
            if employee.inn == inn:
                raise ValueError("сотрудник с таким ИНН уже существует")
