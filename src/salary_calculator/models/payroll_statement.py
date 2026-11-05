from dataclasses import dataclass
from decimal import Decimal

from .payroll_result import PayrollResult
from .period import Period


@dataclass(frozen=True)
class PayrollStatement:
    """Содержит месячную ведомость с результатами всех сотрудников."""

    period: Period
    organization_name: str
    results: tuple[PayrollResult, ...]
    source_revision: int

    @property
    def total_accrued(self) -> Decimal:
        """Возвращает общую сумму начисления."""

        return sum((item.accrued for item in self.results), Decimal("0.00"))

    @property
    def total_tax(self) -> Decimal:
        """Возвращает общую сумму НДФЛ."""

        return sum((item.tax for item in self.results), Decimal("0.00"))

    @property
    def total_to_pay(self) -> Decimal:
        """Возвращает общую сумму к выплате."""

        return sum((item.amount_to_pay for item in self.results), Decimal("0.00"))