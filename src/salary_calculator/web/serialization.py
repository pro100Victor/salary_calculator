"""Перевод предметных объектов в JSON без ORM-объектов и вычисления зарплаты."""

from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any


def to_json(value: Any) -> Any:
    """Сохраняет точные Decimal строками, а даты переводит в ISO-формат."""

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_json(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): to_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_json(item) for item in value]
    return value
