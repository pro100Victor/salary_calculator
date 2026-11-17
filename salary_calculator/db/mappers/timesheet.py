"""Состав табеля восстанавливается независимо от заполненности строк."""

from salary_calculator.db.mappers.period import PeriodMapper
from salary_calculator.db.mappers.timesheet_entry import TimesheetEntryMapper
from salary_calculator.db.models import TimesheetRow
from salary_calculator.models import Timesheet


class TimesheetMapper:
    """Переносит состав, строки и версию в самостоятельный dataclass."""

    @staticmethod
    def to_domain(row: TimesheetRow) -> Timesheet:
        """Включает в employee_ids также незаполненные строки."""
        entries = {}
        for item in row.rows:
            entry = TimesheetEntryMapper.to_domain(item)
            if entry is not None:
                entries[item.employee_id] = entry
        return Timesheet(
            PeriodMapper.to_domain(row.period),
            row.shift_norm,
            tuple(item.employee_id for item in row.rows),
            entries,
            row.revision,
            row.closed,
        )

    @staticmethod
    def apply(value: Timesheet, row: TimesheetRow) -> None:
        """Переносит заголовок; состав и строки синхронизирует репозиторий."""
        row.shift_norm = value.shift_norm
        row.revision = value.revision
        row.closed = value.closed
