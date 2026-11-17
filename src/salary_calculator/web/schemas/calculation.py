"""Данные формы calculation."""

from pydantic import BaseModel, ConfigDict, StrictBool


class CalculationInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    replace_existing: StrictBool = False
