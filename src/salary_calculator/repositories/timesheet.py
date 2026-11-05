from abc import ABC, abstractmethod

from salary_calculator.models import Period, Timesheet


class TimesheetRepository(ABC):
    """Определяет обязательные операции хранилища табелей."""

    @abstractmethod
    def save(self, timesheet: Timesheet) -> None:
        """Сохраняет табель за один месяц."""

    @abstractmethod
    def get(self, period: Period) -> Timesheet:
        """Возвращает табель за выбранный месяц."""

    @abstractmethod
    def contains(self, period: Period) -> bool:
        """Проверяет существование табеля за выбранный месяц."""


class InMemoryTimesheetRepository(TimesheetRepository):
    """Хранит месячные табели в словаре по периоду."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище табелей."""

        self._items: dict[Period, Timesheet] = {}

    def save(self, timesheet: Timesheet) -> None:
        """Сохраняет табель в оперативной памяти."""

        self._items[timesheet.period] = timesheet

    def get(self, period: Period) -> Timesheet:
        """Возвращает существующий табель."""

        try:
            return self._items[period]
        except KeyError as error:
            raise LookupError(f"табель за {period} не найден") from error

    def contains(self, period: Period) -> bool:
        """Сообщает, существует ли табель за период."""

        return period in self._items