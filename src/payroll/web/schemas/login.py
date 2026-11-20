"""Данные формы login."""

from pydantic import BaseModel, ConfigDict


class LoginInput(BaseModel):
    """Принимает только объявленные поля формы."""

    model_config = ConfigDict(extra="forbid")

    username: str
    password: str
