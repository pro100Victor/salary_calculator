"""Данные формы position."""

from pydantic import BaseModel, ConfigDict


class PositionInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    name: str
    base_rate: str
    seniority_percent: str
