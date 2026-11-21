"""Контракт и InMemory-хранилище кадровых карточек."""

from abc import ABC, abstractmethod
from dataclasses import replace

from payroll.models import Employee


class EmployeeRepository(ABC):
    """Определяет операции хранения сотрудников независимо от реализации."""

    @abstractmethod
    def save(self, employee: Employee) -> Employee:
        """Сохраняет карточку; при ID = 0 назначает новый идентификатор."""

    @abstractmethod
    def get(self, employee_id: int) -> Employee:
        """Возвращает карточку или поднимает LookupError."""

    @abstractmethod
    def list_all(self) -> list[Employee]:
        """Возвращает все карточки сотрудников."""

    def find_by_inn(self, inn: str) -> Employee | None:
        """Находит карточку по ИНН или возвращает None."""

        return next((item for item in self.list_all() if item.inn == inn), None)


class InMemoryEmployeeRepository(EmployeeRepository):
    """Хранит неизменяемые карточки в словаре по идентификатору."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище и счётчик идентификаторов."""

        self._items: dict[int, Employee] = {}
        self._next_id = 1

    def save(self, employee: Employee) -> Employee:
        """Назначает ID новой карточке и сохраняет её."""

        duplicate = self.find_by_inn(employee.inn)
        if duplicate is not None and (
            employee.employee_id == 0 or duplicate.employee_id != employee.employee_id
        ):
            raise ValueError("сотрудник с таким ИНН уже существует")
        if employee.employee_id == 0:
            employee = replace(employee, employee_id=self._next_id)
        self._items[employee.employee_id] = employee
        self._next_id = max(self._next_id, employee.employee_id + 1)
        return employee

    def get(self, employee_id: int) -> Employee:
        """Находит карточку по идентификатору."""

        try:
            return self._items[employee_id]
        except KeyError as error:
            raise LookupError(f"сотрудник с ID {employee_id} не найден") from error

    def list_all(self) -> list[Employee]:
        """Возвращает карточки по возрастанию идентификатора."""

        return sorted(self._items.values(), key=lambda item: item.employee_id)
