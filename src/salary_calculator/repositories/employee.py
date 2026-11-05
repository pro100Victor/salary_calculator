from abc import ABC, abstractmethod

from salary_calculator.models import Employee


class EmployeeRepository(ABC):
    """Определяет обязательные операции хранилища сотрудников."""

    @abstractmethod
    def save(self, employee: Employee) -> None:
        """Сохраняет новую или изменённую кадровую карточку."""

    @abstractmethod
    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по идентификатору."""

    @abstractmethod
    def list_all(self) -> list[Employee]:
        """Возвращает все карточки сотрудников."""

class InMemoryEmployeeRepository(EmployeeRepository):
    """Хранит кадровые карточки в словаре по идентификатору."""

    def __init__(self) -> None:
        """Создаёт пустой справочник."""

        self._items: dict[int, Employee] = {}

    def save(self, employee: Employee) -> None:
        """Добавляет или заменяет карточку сотрудника."""

        self._items[employee.employee_id] = employee

    def get(self, employee_id: int) -> Employee:
        """Находит сотрудника по его ID."""

        try:
            return self._items[employee_id]
        except KeyError as error:
            raise LookupError(f"сотрудник с ID {employee_id} не найден") from error

    def list_all(self) -> list[Employee]:
        """Возвращает список всех сотрудников."""

        return list(self._items.values())