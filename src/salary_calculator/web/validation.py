"""Привязка ошибок существующих валидаторов к полям формы."""

from collections.abc import Callable
from typing import TypeVar

from fastapi import HTTPException

T = TypeVar("T")


def checked(field: str, validate: Callable[[], T]) -> T:
    """Не дублирует правило модели; добавляет имя поля к его ошибке."""

    try:
        return validate()
    except (ValueError, LookupError) as error:
        raise HTTPException(
            400, detail={"message": str(error), "fields": {field: str(error)}}
        ) from error
