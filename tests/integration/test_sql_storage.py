"""Интеграционные проверки SQL-хранилища на живом PostgreSQL."""

import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest

from salary_calculator.application.sql_provider import SQLServiceProvider
from salary_calculator.models import Period

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="нужен запущенный отдельный PostgreSQL и TEST_DATABASE_URL"
)

PERIOD = Period(2026, 5)
INN_ONE = "123456789012"
INN_TWO = "223456789012"


@pytest.fixture()
def provider() -> Iterator[SQLServiceProvider]:
    """Создаёт провайдер и очищает таблицы перед тестом."""

    storage = SQLServiceProvider(DATABASE_URL)
    with storage.engine.begin() as connection:
        from salary_calculator.db.base import Base

        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield storage
    storage.engine.dispose()


def test_storage_mode(provider: SQLServiceProvider) -> None:
    """Интерфейс видит честное название хранилища."""

    assert "PostgreSQL" in provider.storage_mode


def test_organization_requires_setup(provider: SQLServiceProvider) -> None:
    """Без настройки организация недоступна с прежним сообщением."""

    with provider.operation() as services:
        with pytest.raises(LookupError, match="сначала настройте организацию"):
            services.organization.get_organization()


def test_organization_and_positions_persist(provider: SQLServiceProvider) -> None:
    """Реквизиты и должности живут между операциями."""

    with provider.operation() as services:
        services.organization.set_organization(
            "Ромашка", "1234567890", "123456789", "Волгоград, пр. Ленина 1"
        )
        services.organization.set_position("Мастер", "2500", "0")
    with provider.operation() as services:
        assert services.organization.get_organization().name == "Ромашка"
        assert services.organization.get_position("Мастер").base_rate == Decimal(
            "2500.00"
        )


def test_employee_gets_id_from_database(provider: SQLServiceProvider) -> None:
    """Идентификатор назначает база, а не max+1."""

    with provider.operation() as services:
        services.organization.set_position("Мастер", "2500", "0")
        first = services.employees.add_employee(
            "Иванов И. И.", INN_ONE, "Мастер", date(2020, 1, 10), 3
        )
        second = services.employees.add_employee(
            "Петров П. П.", INN_TWO, "Мастер", date(2021, 6, 1), 0
        )
    with provider.operation() as services:
        assert (
            services.employees.get_employee_by_id(first.employee_id).full_name
            == "Иванов И. И."
        )
        assert (
            services.employees.get_employee_by_id(second.employee_id).employee_id != 0
        )


def test_duplicate_inn_rejected(provider: SQLServiceProvider) -> None:
    """Повторный ИНН отклоняется, прежние данные не искажаются."""

    with provider.operation() as services:
        services.organization.set_position("Мастер", "2500", "0")
        services.employees.add_employee(
            "Иванов И. И.", INN_ONE, "Мастер", date(2020, 1, 10), 0
        )
        with pytest.raises(ValueError, match="ИНН"):
            services.employees.add_employee(
                "Дубль Д. Д.", INN_ONE, "Мастер", date(2021, 1, 1), 0
            )


def test_payroll_calculation_by_test_plan(provider: SQLServiceProvider) -> None:
    """Сценарий TEST_PLAN: 2500 × 20 смен → 50000 / 6500 / 43500."""

    with provider.operation() as services:
        services.organization.set_organization(
            "Ромашка", "1234567890", "123456789", "Волгоград, пр. Ленина 1"
        )
        services.organization.set_position("Мастер", "2500", "0")
        first = services.employees.add_employee(
            "Иванов И. И.", INN_ONE, "Мастер", date(2020, 1, 10), 0
        )
        second = services.employees.add_employee(
            "Петров П. П.", INN_TWO, "Мастер", date(2021, 6, 1), 0
        )
        services.calendar.set_norm(PERIOD, 22)
        services.timesheets.generate(PERIOD)
        for employee_id in (first.employee_id, second.employee_id):
            services.timesheets.fill(PERIOD, employee_id, 20, 1, 1)
        services.payroll.calculate_period(PERIOD)
    with provider.operation() as services:
        stored = services.payroll.get_statement(PERIOD)
        assert stored is not None
        assert len(stored.results) == 2
        for item in stored.results:
            assert item.accrued == Decimal("50000.00")
            assert item.tax == Decimal("6500.00")
            assert item.amount_to_pay == Decimal("43500.00")


def test_close_requires_current_statement(provider: SQLServiceProvider) -> None:
    """Закрытие запрещено со старой версией ведомости; после правки — тоже."""

    with provider.operation() as services:
        services.organization.set_organization(
            "Ромашка", "1234567890", "123456789", "Волгоград, пр. Ленина 1"
        )
        services.organization.set_position("Мастер", "2500", "0")
        first = services.employees.add_employee(
            "Иванов И. И.", INN_ONE, "Мастер", date(2020, 1, 10), 0
        )
        services.calendar.set_norm(PERIOD, 22)
        services.timesheets.generate(PERIOD)
        services.timesheets.fill(PERIOD, first.employee_id, 22, 0, 0)
        services.payroll.calculate_period(PERIOD)

    with provider.operation() as services:
        services.timesheets.fill(PERIOD, first.employee_id, 21, 1, 0)
        with pytest.raises(ValueError, match="пересчитайте"):
            services.payroll.close_period(PERIOD)
        services.payroll.calculate_period(PERIOD, replace_existing=True)
        services.payroll.close_period(PERIOD)
        assert services.timesheets.get(PERIOD).closed

    with provider.operation() as services:
        with pytest.raises(ValueError, match="закрыт"):
            services.timesheets.fill(PERIOD, first.employee_id, 1, 0, 0)
        with pytest.raises(ValueError, match="нельзя"):
            services.payroll.calculate_period(PERIOD, replace_existing=True)
