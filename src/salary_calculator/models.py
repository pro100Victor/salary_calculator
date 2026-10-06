"""Данные организации, сотрудников, табеля и расчётной ведомости."""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, order=True)
class Period:
    """Обозначает календарный месяц расчёта."""

    year: int
    month: int

    def __post_init__(self) -> None:
        """Проверяет существование выбранного месяца."""

        if not 1 <= self.year <= 9999 or not 1 <= self.month <= 12:
            raise ValueError("укажите корректный год и месяц")

    @property
    def start(self) -> date:
        """Возвращает первый день месяца."""

        return date(self.year, self.month, 1)

    @property
    def end(self) -> date:
        """Возвращает последний день месяца."""

        return date(self.year, self.month, monthrange(self.year, self.month)[1])

    def __str__(self) -> str:
        """Представляет период в формате ММ.ГГГГ."""

        return f"{self.month:02d}.{self.year}"


@dataclass(frozen=True)
class Organization:
    """Содержит реквизиты малого предприятия."""

    name: str
    inn: str
    kpp: str
    address: str


@dataclass(frozen=True)
class Position:
    """Задаёт базовую ставку и надбавку за полный год стажа."""

    name: str
    base_rate: Decimal
    seniority_percent: Decimal


@dataclass(frozen=True)
class Employee:
    """Хранит кадровую карточку и рассчитанную ставку за смену."""

    employee_id: int
    full_name: str
    inn: str
    position: str
    hire_date: date
    experience_years: int
    rate_per_shift: Decimal
    dismissal_date: date | None = None

    @property
    def status(self) -> str:
        """Показывает, числится ли сотрудник в штате сейчас."""

        return "Уволен" if self.dismissal_date else "В штате"

    def employed_in(self, period: Period) -> bool:
        """Проверяет пересечение периода с датами работы сотрудника."""

        return self.hire_date <= period.end and (
            self.dismissal_date is None or self.dismissal_date >= period.start
        )


@dataclass(frozen=True)
class TimesheetEntry:
    """Содержит заполненную строку табеля одного сотрудника."""

    employee_id: int
    worked_shifts: int
    sick_days: int
    vacation_days: int

    @property
    def total_days(self) -> int:
        """Возвращает сумму смен и дней отсутствия."""

        return self.worked_shifts + self.sick_days + self.vacation_days


@dataclass
class Timesheet:
    """Хранит InMemory-табель за расчётный месяц."""

    period: Period
    shift_norm: int
    employee_ids: tuple[int, ...]
    entries: dict[int, TimesheetEntry] = field(default_factory=dict)
    revision: int = 0
    closed: bool = False


@dataclass(frozen=True)
class PayrollResult:
    """Содержит результат расчёта зарплаты одного сотрудника."""

    employee: Employee
    worked_shifts: int
    sick_days: int
    vacation_days: int
    accrued: Decimal
    tax: Decimal
    amount_to_pay: Decimal


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
