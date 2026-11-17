"""Хранение ручной нормы отдельно от календарного вычисления."""

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from salary_calculator.db.period_lookup import ensure_period, find_period
from salary_calculator.models import Period


class NormRepository(ABC):
    """Возвращает None, если ручная норма ещё не задана."""

    @abstractmethod
    def get(self, period: Period) -> int | None:
        """Читает ручную норму периода."""

    @abstractmethod
    def save(self, period: Period, shifts: int) -> None:
        """Сохраняет норму, не выполняя commit."""


class InMemoryNormRepository(NormRepository):
    """Хранит ручные нормы в памяти."""

    def __init__(self) -> None:
        """Создаёт словарь периодов."""
        self._items: dict[Period, int] = {}

    def get(self, period: Period) -> int | None:
        """Возвращает заданную норму либо None."""
        return self._items.get(period)

    def save(self, period: Period, shifts: int) -> None:
        """Запоминает ручную норму."""
        self._items[period] = shifts


class SQLAlchemyNormRepository(NormRepository):
    """Сохраняет настройку периода и проверяет фиксацию нормы табелем."""

    def __init__(self, session: Session) -> None:
        """Принимает внешнюю Session."""
        self._session = session

    def get(self, period: Period) -> int | None:
        """Читает без создания периода."""
        row = find_period(self._session, period, lock=True)
        return row.norm_override if row else None

    def save(self, period: Period, shifts: int) -> None:
        """Блокирует период и запрещает менять норму сформированного табеля."""
        row = ensure_period(self._session, period)
        if row.timesheet is not None:
            raise ValueError("табель уже создан; норма периода зафиксирована")
        row.norm_override = shifts
        self._session.flush()
