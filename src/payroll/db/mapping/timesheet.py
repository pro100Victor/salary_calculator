"""Маппер TimesheetMapper."""

from payroll.db.models import (
    TimesheetEntryRow,
    TimesheetRow,
)
from payroll.models import (
    Timesheet,
)

from .period import PeriodMapper
from .timesheet_entry import TimesheetEntryMapper


class TimesheetMapper:
    """Преобразует ORM-данные в предметные модели без открытой Session."""

    @staticmethod
    def to_domain(header: TimesheetRow, rows: list[TimesheetEntryRow]) -> Timesheet:
        """Собирает доменный табель: участники из всех строк, записи из заполненных."""

        entries = {}
        for row in rows:
            entry = TimesheetEntryMapper.to_domain(row)
            if entry is not None:
                entries[row.employee_id] = entry
        return Timesheet(
            PeriodMapper.to_domain(header.year, header.month),
            header.shift_norm,
            tuple(row.employee_id for row in rows),
            entries,
            header.revision,
            header.closed,
        )
