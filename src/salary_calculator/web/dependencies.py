"""Открытие сервисов на один HTTP-запрос и проверка сеанса."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from salary_calculator.application.services import ApplicationServices


def require_login(request: Request) -> None:
    """Проверяет HttpOnly-cookie до обращения к сервисам."""

    request.app.state.sessions.require(request.cookies.get("salary_session", ""))


def get_services(request: Request) -> Iterator[ApplicationServices]:
    """Закрывает операцию провайдера до отправки успешного ответа."""

    with request.app.state.provider.operation() as services:
        yield services


Services = Annotated[ApplicationServices, Depends(get_services, scope="function")]
