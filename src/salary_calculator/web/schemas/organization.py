"""Данные формы organization."""

from pydantic import BaseModel, ConfigDict


class OrganizationInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    name: str
    inn: str
    kpp: str
    address: str
