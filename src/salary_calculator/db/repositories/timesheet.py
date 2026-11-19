"""SQL-репозиторий табелей: шапка плюс строки участников."""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from salary_calculator.db import mappers
from salary_calculator.db.models import TimesheetEntryRow, TimesheetRow
from salary_calculator.models import Period, Timesheet
from salary_calculator.repositories.timesheet import TimesheetRepository


class SqlTimesheetRepository(TimesheetRepository):
    """Сохраняет табель целиком; чтение блокирует строку шапки."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def save(self, timesheet: Timesheet) -> Timesheet:
        """Создаёт табель или перезаписывает строки по текущему состоянию."""

        header = self._session.execute(
            select(TimesheetRow)
            .where(
                TimesheetRow.year == timesheet.period.year,
                TimesheetRow.month == timesheet.period.month,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if header is None:
            header = TimesheetRow(
                year=timesheet.period.year,
                month=timesheet.period.month,
                shift_norm=timesheet.shift_norm,
                revision=timesheet.revision,
                closed=timesheet.closed,
            )
            self._session.add(header)
            self._session.flush()
        else:
            header.shift_norm = timesheet.shift_norm
            header.revision = timesheet.revision
            header.closed = timesheet.closed
            self._session.execute(
                delete(TimesheetEntryRow).where(
                    TimesheetEntryRow.timesheet_id == header.timesheet_id
                )
            )
        for employee_id in timesheet.employee_ids:
            entry = timesheet.entries.get(employee_id)
            self._session.add(
                TimesheetEntryRow(
                    timesheet_id=header.timesheet_id,
                    employee_id=employee_id,
                    worked_shifts=entry.worked_shifts if entry else None,
                    sick_days=entry.sick_days if entry else None,
                    vacation_days=entry.vacation_days if entry else None,
                )
            )
        self._session.flush()
        return timesheet

    def get(self, period: Period) -> Timesheet:
        """Возвращает табель, блокируя шапку от параллельной правки."""

        header = self._session.execute(
            select(TimesheetRow)
            .where(TimesheetRow.year == period.year, TimesheetRow.month == period.month)
            .with_for_update()
        ).scalar_one_or_none()
        if header is None:
            raise LookupError(f"табель за {period} не найден")
        rows = self._session.execute(
            select(TimesheetEntryRow)
            .where(TimesheetEntryRow.timesheet_id == header.timesheet_id)
            .order_by(TimesheetEntryRow.employee_id)
        ).scalars().all()
        return mappers.timesheet_to_domain(header, rows)

    def contains(self, period: Period) -> bool:
        """Проверяет существование табеля за период."""

        return bool(
            self._session.execute(
                select(func.count())
                .select_from(TimesheetRow)
                .where(TimesheetRow.year == period.year, TimesheetRow.month == period.month)
            ).scalar_one()
        )
