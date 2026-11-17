"""Восстановление ведомости с историческими расчётными листками."""

from salary_calculator.db.mappers.payroll_result import PayrollResultMapper
from salary_calculator.db.mappers.period import PeriodMapper
from salary_calculator.db.models import PayrollStatementRow
from salary_calculator.models import PayrollStatement


class PayrollStatementMapper:
    """Создаёт полностью загруженную ведомость без зависимости от Session."""

    @staticmethod
    def to_domain(row: PayrollStatementRow) -> PayrollStatement:
        """Включает результаты, версию табеля и название организации-снимок."""
        return PayrollStatement(
            PeriodMapper.to_domain(row.timesheet.period),
            row.organization_name,
            tuple(PayrollResultMapper.to_domain(item) for item in row.results),
            row.source_revision,
        )

    @staticmethod
    def apply(value: PayrollStatement, row: PayrollStatementRow) -> None:
        """Копирует заголовок; строки синхронизирует репозиторий."""
        row.organization_name = value.organization_name
        row.source_revision = value.source_revision
