"""Данные формы norm."""

from pydantic import BaseModel, ConfigDict, StrictInt


class NormInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    shifts: StrictInt
