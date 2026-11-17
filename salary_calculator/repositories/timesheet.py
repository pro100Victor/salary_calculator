from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from salary_calculator.db.mappers.timesheet import TimesheetMapper
from salary_calculator.db.mappers.timesheet_entry import TimesheetEntryMapper
from salary_calculator.db.models import TimesheetEntryRow, TimesheetRow
from salary_calculator.db.period_lookup import ensure_period, find_period
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


class SQLAlchemyTimesheetRepository(TimesheetRepository):
    """Хранит состав и строки табеля под блокировкой общего периода."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей транзакции."""
        self._session = session

    def _get_row(self, period: Period) -> TimesheetRow | None:
        """Загружает связи, не оставляя ленивых обращений в dataclass."""
        period_row = find_period(self._session, period, lock=True)
        if period_row is None:
            return None
        statement = (
            select(TimesheetRow)
            .where(TimesheetRow.period_id == period_row.id)
            .options(joinedload(TimesheetRow.period), selectinload(TimesheetRow.rows))
            .execution_options(populate_existing=True)
        )
        return self._session.scalar(statement)

    def contains(self, period: Period) -> bool:
        """Проверяет существование, не создавая табель."""
        return self._get_row(period) is not None

    def get(self, period: Period) -> Timesheet:
        """Удерживает блокировку периода до commit/rollback провайдера."""
        row = self._get_row(period)
        if row is None:
            raise LookupError(f"табель за {period} не найден")
        return TimesheetMapper.to_domain(row)

    def save(self, timesheet: Timesheet) -> None:
        """Явно сохраняет mutable dataclass и все его строки."""
        period_row = ensure_period(self._session, timesheet.period)
        row = self._get_row(timesheet.period)
        if row is None:
            row = TimesheetRow(period=period_row)
            self._session.add(row)
            if (
                period_row.norm_override is not None
                and period_row.norm_override != timesheet.shift_norm
            ):
                raise ValueError(
                    "норма периода изменилась; повторите формирование табеля"
                )
        elif row.closed:
            raise ValueError("расчётный период закрыт")
        elif row.revision > timesheet.revision:
            raise ValueError("табель изменён другой операцией; повторите ввод")
        elif row.shift_norm != timesheet.shift_norm:
            raise ValueError("норма сформированного табеля зафиксирована")
        if timesheet.shift_norm < 1 or timesheet.shift_norm > timesheet.period.end.day:
            raise ValueError("некорректная норма табеля")
        if len(set(timesheet.employee_ids)) != len(timesheet.employee_ids):
            raise ValueError("повтор сотрудника в табеле")
        if not set(timesheet.entries).issubset(timesheet.employee_ids):
            raise ValueError("сотрудника нет в составе табеля")
        TimesheetMapper.apply(timesheet, row)
        existing = {item.employee_id: item for item in row.rows}
        if existing and set(existing) != set(timesheet.employee_ids):
            raise ValueError("состав сформированного табеля менять нельзя")
        for employee_id in timesheet.employee_ids:
            entry = timesheet.entries.get(employee_id)
            if entry is not None:
                timesheet.validate_days(entry.total_days)
            item = existing.get(employee_id)
            if item is None:
                item = TimesheetEntryRow(employee_id=employee_id)
                row.rows.append(item)
            TimesheetEntryMapper.apply(entry, item)
        self._session.flush()
