"""Переносимые SQL-выражения ограничений схемы."""


def digits_only(column: str) -> str:
    """Проверяет ASCII-цифры средствами PostgreSQL и SQLite, сохраняя нули."""
    expression = column
    for digit in "0123456789":
        expression = f"replace({expression}, '{digit}', '')"
    return f"length({expression}) = 0"
