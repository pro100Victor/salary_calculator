"""SQL-репозиторий ручных норм смен по расчётным периодам."""

from salary_calculator.repositories.calendar_norm import CalendarNormRepository
from sqlalchemy import select
from sqlalchemy.orm import Session

from salary_calculator.db.locking import lock_period
from salary_calculator.db.models import CalendarNormRow
from salary_calculator.models import Period


class SqlCalendarNormRepository(CalendarNormRepository):
    """Хранит переопределения нормы; отсутствие записи означает будни."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def get(self, period: Period) -> int | None:
        """Возвращает сохранённую норму или None, если она не задана."""

        lock_period(self._session, period)
        row = self._session.execute(
            select(CalendarNormRow).where(
                CalendarNormRow.year == period.year,
                CalendarNormRow.month == period.month,
            )
        ).scalar_one_or_none()
        return None if row is None else row.shifts

    def set(self, period: Period, shifts: int) -> None:
        """Создаёт или обновляет норму для периода."""

        lock_period(self._session, period)
        from salary_calculator.db.models import TimesheetRow

        existing = self._session.execute(
            select(TimesheetRow.timesheet_id).where(
                TimesheetRow.year == period.year, TimesheetRow.month == period.month
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("после создания табеля норму смен менять нельзя")

        row = self._session.execute(
            select(CalendarNormRow)
            .where(
                CalendarNormRow.year == period.year,
                CalendarNormRow.month == period.month,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if row is None:
            self._session.add(
                CalendarNormRow(year=period.year, month=period.month, shifts=shifts)
            )
        else:
            row.shifts = shifts
        self._session.flush()
