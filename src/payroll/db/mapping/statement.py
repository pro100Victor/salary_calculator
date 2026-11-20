"""Маппер StatementMapper."""

from payroll.db.models import (
    StatementResultRow,
    StatementRow,
)
from payroll.models import (
    PayrollStatement,
)

from .payroll_result import PayrollResultMapper
from .period import PeriodMapper


class StatementMapper:
    """Преобразует ORM-данные в предметные модели без открытой Session."""

    @staticmethod
    def to_domain(
        header: StatementRow, rows: list[StatementResultRow]
    ) -> PayrollStatement:
        """Собирает ведомость со снимками сотрудников из строк результата."""

        results = [PayrollResultMapper.to_domain(row) for row in rows]
        return PayrollStatement(
            PeriodMapper.to_domain(header.year, header.month),
            header.organization_name,
            tuple(results),
            header.source_revision,
        )
