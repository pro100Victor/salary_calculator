"""SQL-репозиторий расчётных ведомостей со строками-снимками."""

from salary_calculator.repositories.statement import StatementRepository
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from salary_calculator.db import mappers
from salary_calculator.db.locking import lock_period
from salary_calculator.db.models import StatementResultRow, StatementRow
from salary_calculator.models import PayrollStatement, Period


class SqlStatementRepository(StatementRepository):
    """Заменяет ведомость целиком: проверка прошла — данные зафиксированы."""

    def __init__(self, session: Session) -> None:
        """Принимает Session текущей операции."""

        self._session = session

    def save(self, statement: PayrollStatement) -> PayrollStatement:
        """Создаёт или перезаписывает ведомость вместе со всеми строками."""

        lock_period(self._session, statement.period)
        header = self._session.execute(
            select(StatementRow)
            .where(
                StatementRow.year == statement.period.year,
                StatementRow.month == statement.period.month,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if header is None:
            header = StatementRow(
                year=statement.period.year,
                month=statement.period.month,
                organization_name=statement.organization_name,
                source_revision=statement.source_revision,
            )
            self._session.add(header)
            self._session.flush()
        else:
            header.organization_name = statement.organization_name
            header.source_revision = statement.source_revision
            self._session.execute(
                delete(StatementResultRow).where(
                    StatementResultRow.statement_id == header.statement_id
                )
            )
        for result in statement.results:
            self._session.add(
                StatementResultRow(
                    statement_id=header.statement_id,
                    employee_id=result.employee.employee_id,
                    **mappers.result_fields(result),
                )
            )
        self._session.flush()
        return statement

    def get(self, period: Period) -> PayrollStatement:
        """Возвращает ведомость за период или поднимает знакомую ошибку."""

        lock_period(self._session, period)
        header = self._session.execute(
            select(StatementRow).where(
                StatementRow.year == period.year, StatementRow.month == period.month
            )
        ).scalar_one_or_none()
        if header is None:
            raise LookupError(f"ведомость за {period} не найдена")
        rows = (
            self._session.execute(
                select(StatementResultRow)
                .where(StatementResultRow.statement_id == header.statement_id)
                .order_by(StatementResultRow.employee_id)
            )
            .scalars()
            .all()
        )
        return mappers.statement_to_domain(header, rows)

    def contains(self, period: Period) -> bool:
        """Проверяет существование ведомости за период."""

        lock_period(self._session, period)
        return bool(
            self._session.execute(
                select(func.count())
                .select_from(StatementRow)
                .where(
                    StatementRow.year == period.year, StatementRow.month == period.month
                )
            ).scalar_one()
        )
