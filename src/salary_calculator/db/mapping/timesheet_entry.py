"""Преобразование заполненной строки табеля."""

from salary_calculator.db.models import TimesheetEntryRow
from salary_calculator.models import TimesheetEntry


class TimesheetEntryMapper:
    """Отличает отсутствующий ввод от явно заданных нулей."""

    @staticmethod
    def to_domain(row: TimesheetEntryRow) -> TimesheetEntry | None:
        """Возвращает None для незаполненной строки."""

        if row.worked_shifts is None:
            return None
        return TimesheetEntry(
            row.employee_id, row.worked_shifts, row.sick_days, row.vacation_days
        )
