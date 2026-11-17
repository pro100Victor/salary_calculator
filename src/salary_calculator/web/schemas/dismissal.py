"""Данные формы dismissal."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class DismissalInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    dismissal_date: date
