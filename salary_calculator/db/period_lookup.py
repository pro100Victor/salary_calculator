"""Поиск и блокировка периода в текущей внешней транзакции."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from salary_calculator.db.models import OrganizationRow, PeriodRow
from salary_calculator.models import Period


def find_period(
    session: Session, period: Period, lock: bool = False
) -> PeriodRow | None:
    """По запросу блокирует период для согласованного заполнения и закрытия."""
    statement = select(PeriodRow).where(
        PeriodRow.organization_id == 1,
        PeriodRow.year == period.year,
        PeriodRow.month == period.month,
    )
    if lock:
        statement = statement.with_for_update()
    return session.scalar(statement.execution_options(populate_existing=True))


def ensure_period(session: Session, period: Period) -> PeriodRow:
    """Создаёт период под блокировкой организации, не создавая таблицы БД."""
    existing = find_period(session, period, lock=True)
    if existing is not None:
        return existing
    organization = session.scalar(
        select(OrganizationRow).where(OrganizationRow.id == 1).with_for_update()
    )
    if organization is None:
        raise LookupError("сначала настройте организацию")
    row = find_period(session, period, lock=True)
    if row is None:
        row = PeriodRow(organization_id=1, year=period.year, month=period.month)
        session.add(row)
        session.flush()
    return row
