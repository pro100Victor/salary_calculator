from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

KOPECK = Decimal("0.01")

def as_decimal(value: Decimal | str | float) -> Decimal:
    """Преобразует число в конечный Decimal без двоичной ошибки float."""

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("введите корректную денежную сумму") from error

    if not number.is_finite():
        raise ValueError("денежная сумма должна быть конечной")

    return number


@dataclass(frozen=True)
class Position:
    """Задаёт базовую ставку и надбавку за полный год стажа."""

    name: str
    base_rate: Decimal
    seniority_percent: Decimal

    @staticmethod
    def validate_position_name(value: str) -> str:
        """Проверяет название должности."""
        name = value.strip()
        if not name:
            raise ValueError("название должности не может быть пустым")
        return name

    @staticmethod
    def validate_base_rate(value: Decimal | str | float) -> Decimal:
        """Проверяет базовую ставку."""
        rate = as_decimal(value)
        if rate > Decimal(1000000000):
            raise ValueError("ставка за смену слишком велика")
        if rate <= 0 or rate != rate.quantize(KOPECK):
            raise ValueError("ставка должна быть положительной суммой с двумя знаками")
        return rate

    @staticmethod
    def validate_seniority_percent(value: Decimal | str | float) -> Decimal:
        """Проверяет надбавку за стаж."""
        percent = as_decimal(value)
        if not 0 <= percent <= 100:
            raise ValueError("надбавка за год стажа должна быть от 0 до 100%")
        return percent

    def __post_init__(self) -> None:
        """Проверяет поля при создании должности."""
        self.validate_position_name(self.name)
        self.validate_base_rate(self.base_rate)
        self.validate_seniority_percent(self.seniority_percent)