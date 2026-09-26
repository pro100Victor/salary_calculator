"""Функции безопасного ввода значений через терминал."""

import math
from collections.abc import Callable


class InputReader:
    """Читает и проверяет пользовательский ввод."""

    def __init__(
        self,
        input_function: Callable[[str], str] | None = None,
        output_function: Callable[[str], None] | None = None,
    ) -> None:
        """Сохраняет функции ввода и вывода для дальнейшего использования."""

        self._input = input_function or input
        self._output = output_function or print

    def read_non_empty(self, message: str) -> str:
        """Читает непустую строку."""

        while True:
            value = self._input(message).strip()

            if value:
                return value

            self._output("ошибка: значение не должно быть пустым")

    def read_int(
        self,
        message: str,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int:
        """Читает целое число в заданном диапазоне."""

        while True:
            value = self._input(message).strip()

            try:
                number = int(value)
            except ValueError:
                self._output("ошибка: введите целое число")
                continue

            if minimum is not None and number < minimum:
                self._output(f"ошибка: число должно быть не меньше {minimum}")
                continue

            if maximum is not None and number > maximum:
                self._output(f"ошибка: число должно быть не больше {maximum}")
                continue

            return number

    def read_float(
        self,
        message: str,
        minimum: float | None = None,
    ) -> float:
        """Читает конечное дробное число с точкой или запятой."""

        while True:
            value = self._input(message).strip().replace(",", ".")

            try:
                number = float(value)
            except ValueError:
                self._output("ошибка: введите число")
                continue

            if not math.isfinite(number):
                self._output("ошибка: введите конечное число")
                continue

            if minimum is not None and number < minimum:
                self._output(f"ошибка: число должно быть не меньше {minimum}")
                continue

            return number
