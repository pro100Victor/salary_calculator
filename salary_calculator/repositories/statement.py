from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from salary_calculator.db.mappers.payroll_result import PayrollResultMapper
from salary_calculator.db.mappers.payroll_statement import PayrollStatementMapper
from salary_calculator.db.models import (
    PayrollResultRow,
    PayrollStatementRow,
    TimesheetRow,
)
from salary_calculator.db.period_lookup import find_period
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


class SQLAlchemyStatementRepository(StatementRepository):
    """Сохраняет ведомость и снимки результатов в транзакции вызывающего кода."""

    def __init__(self, session: Session) -> None:
        """Получает внешнюю Session."""
        self._session = session

    def _get_row(self, period: Period) -> PayrollStatementRow | None:
        """Загружает весь граф, необходимый мапперу, без N+1 сотрудников."""
        period_row = find_period(self._session, period)
        if period_row is None:
            return None
        statement = (
            select(PayrollStatementRow)
            .join(PayrollStatementRow.timesheet)
            .where(TimesheetRow.period_id == period_row.id)
            .options(
                selectinload(PayrollStatementRow.results),
                joinedload(PayrollStatementRow.timesheet).joinedload(
                    TimesheetRow.period
                ),
            )
            .execution_options(populate_existing=True)
        )
        return self._session.scalar(statement)

    def contains(self, period: Period) -> bool:
        """Проверяет наличие сохранённой ведомости."""
        return self._get_row(period) is not None

    def get(self, period: Period) -> PayrollStatement:
        """Возвращает самостоятельную ведомость со снимками карточек."""
        row = self._get_row(period)
        if row is None:
            raise LookupError(f"ведомость за {period} не найдена")
        return PayrollStatementMapper.to_domain(row)

    def save(self, statement: PayrollStatement) -> None:
        """Обновляет существующие строки по ID, не нарушая UNIQUE при перерасчёте."""
        period_row = find_period(self._session, statement.period, lock=True)
        if period_row is None:
            raise LookupError("табель не найден")
        timesheet = self._session.scalar(
            select(TimesheetRow)
            .where(TimesheetRow.period_id == period_row.id)
            .execution_options(populate_existing=True)
        )
        if timesheet is None:
            raise LookupError("табель не найден")
        if timesheet.closed:
            raise ValueError("закрытый период пересчитывать нельзя")
        if statement.source_revision != timesheet.revision:
            raise ValueError("табель изменён; повторите расчёт")
        row = self._get_row(statement.period)
        if row is None:
            row = PayrollStatementRow(timesheet=timesheet)
            self._session.add(row)
        PayrollStatementMapper.apply(statement, row)
        existing = {item.employee_id: item for item in row.results}
        employee_ids = {item.employee.employee_id for item in statement.results}
        if len(employee_ids) != len(statement.results):
            raise ValueError("повтор сотрудника в ведомости")
        for item in tuple(row.results):
            if item.employee_id not in employee_ids:
                row.results.remove(item)
        for result in statement.results:
            item = existing.get(result.employee.employee_id)
            if item is None:
                item = PayrollResultRow()
                row.results.append(item)
            PayrollResultMapper.apply(result, item)
        self._session.flush()
