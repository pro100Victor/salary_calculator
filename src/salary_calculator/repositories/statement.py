from abc import ABC, abstractmethod

from salary_calculator.models import PayrollStatement, Period


class StatementRepository(ABC):
    """Определяет обязательные операции хранилища ведомостей."""

    @abstractmethod
    def save(self, statement: PayrollStatement) -> None:
        """Сохраняет проверенную расчётную ведомость."""

    @abstractmethod
    def get(self, period: Period) -> PayrollStatement:
        """Возвращает ведомость за выбранный месяц."""

    @abstractmethod
    def contains(self, period: Period) -> bool:
        """Проверяет наличие ранее сформированной ведомости."""


class InMemoryStatementRepository(StatementRepository):
    """Хранит ведомости в оперативной памяти по месяцам."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище ведомостей."""

        self._items: dict[Period, PayrollStatement] = {}

    def save(self, statement: PayrollStatement) -> None:
        """Сохраняет подтверждённую ведомость."""

        self._items[statement.period] = statement

    def get(self, period: Period) -> PayrollStatement:
        """Возвращает ведомость за расчётный месяц."""

        try:
            return self._items[period]
        except KeyError as error:
            raise LookupError(f"ведомость за {period} не найдена") from error

    def contains(self, period: Period) -> bool:
        """Сообщает, существует ли ведомость за период."""

        return period in self._items