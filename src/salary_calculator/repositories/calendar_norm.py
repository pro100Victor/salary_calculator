"""Контракт хранения ручных норм смен по периодам."""

from abc import ABC, abstractmethod

from salary_calculator.models import Period


class CalendarNormRepository(ABC):
    """Определяет обязательные операции хранилища норм календаря."""

    @abstractmethod
    def get(self, period: Period) -> int | None:
        """Возвращает сохранённую норму или None, если она не задана."""

    @abstractmethod
    def set(self, period: Period, shifts: int) -> None:
        """Сохраняет норму для периода."""


class InMemoryCalendarNormRepository(CalendarNormRepository):
    """Хранит нормы в словаре по периоду."""

    def __init__(self) -> None:
        """Создаёт пустой словарь нормативов."""

        self._items: dict[Period, int] = {}

    def get(self, period: Period) -> int | None:
        """Возвращает норму периода или None."""

        return self._items.get(period)

    def set(self, period: Period, shifts: int) -> None:
        """Сохраняет норму периода."""

        self._items[period] = shifts
