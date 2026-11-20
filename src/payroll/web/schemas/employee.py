"""Данные формы employee."""

from datetime import date

from pydantic import BaseModel, ConfigDict, StrictInt


class EmployeeInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    full_name: str
    inn: str
    position: str
    hire_date: date
    experience_years: StrictInt
