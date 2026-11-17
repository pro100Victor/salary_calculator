"""Данные формы entry."""

from pydantic import BaseModel, ConfigDict, StrictInt


class EntryInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    worked_shifts: StrictInt
    sick_days: StrictInt
    vacation_days: StrictInt
