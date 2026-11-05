

from decimal import ROUND_HALF_UP, Decimal

KOPECK = Decimal("0.01")

class TaxCalculator:
    """Удерживает установленный для учебной модели НДФЛ 13%."""

    NDFL_RATE = Decimal("0.13")

    def calculate(self, accrued: Decimal) -> Decimal:
        """Округляет величину удержания до копеек."""

        return (accrued * self.NDFL_RATE).quantize(KOPECK, rounding=ROUND_HALF_UP)
