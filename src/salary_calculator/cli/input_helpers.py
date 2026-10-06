"""Повторный запрос ошибочно введённых чисел и дат."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation


class InputReader:
    """Читает данные пользователя, не прерывая приложение при ошибке."""

    def __init__(
        self,
        input_function: Callable[[str], str] | None = None,
        output_function: Callable[[str], None] | None = None,
    ) -> None:
        """Позволяет подменить ввод и вывод при тестировании."""

        self._input = input_function or input
        self._output = output_function or print

    def read_non_empty(self, prompt: str) -> str:
        """Возвращает непустую строку."""

        while True:
            value = self._input(prompt).strip()
            if value:
                return value
            self._output("ошибка: поле не должно быть пустым")

    def read_optional(self, prompt: str) -> str:
        """Возвращает строку, в том числе пустую."""

        return self._input(prompt).strip()

    def read_int(
        self, prompt: str, minimum: int | None = None, maximum: int | None = None
    ) -> int:
        """Читает целое число в допустимом диапазоне."""

        while True:
            raw = self._input(prompt).strip()
            try:
                value = int(raw)
            except ValueError:
                self._output("ошибка: введите целое число")
                continue
            if minimum is not None and value < minimum:
                self._output(f"ошибка: число должно быть не меньше {minimum}")
                continue
            if maximum is not None and value > maximum:
                self._output(f"ошибка: число должно быть не больше {maximum}")
                continue
            return value

    def read_decimal(self, prompt: str, minimum: Decimal = Decimal("0")) -> Decimal:
        """Читает конечное десятичное число с точкой или запятой."""

        while True:
            raw = self._input(prompt).strip().replace(",", ".")
            try:
                value = Decimal(raw)
            except InvalidOperation:
                self._output("ошибка: введите число")
                continue
            if not value.is_finite() or value < minimum:
                self._output(f"ошибка: введите конечное число не меньше {minimum}")
                continue
            return value

    def read_date(self, prompt: str) -> date:
        """Читает дату в понятном формате ДД.ММ.ГГГГ."""

        while True:
            raw = self._input(prompt).strip()
            try:
                day, month, year = (int(part) for part in raw.split("."))
                return date(year, month, day)
            except (ValueError, TypeError):
                self._output("ошибка: введите дату в формате ДД.ММ.ГГГГ")

    def confirm(self, prompt: str) -> bool:
        """Получает ответ да или нет."""

        while True:
            answer = self._input(f"{prompt} (да/нет): ").strip().casefold()
            if answer in ("да", "д"):
                return True
            if answer in ("нет", "н"):
                return False
            self._output("ошибка: ответьте «да» или «нет»")
