"""Проверки критериев ЛР4 на отдельной PostgreSQL-базе."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from salary_calculator.application.sql_provider import SQLServiceProvider
from salary_calculator.db.models import (
    Base,
    EmployeeRow,
    StatementResultRow,
    TimesheetEntryRow,
    TimesheetRow,
)
from salary_calculator.models import Employee, Period
from salary_calculator.web.app import create_web_application

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="нужна отдельная TEST_DATABASE_URL")
PERIOD = Period(2026, 9)


@pytest.fixture()
def storage() -> Iterator[SQLServiceProvider]:
    """Очищает исключительно явно переданную тестовую базу."""

    provider = SQLServiceProvider(URL)
    with provider.engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield provider
    provider.engine.dispose()


def prepare(storage: SQLServiceProvider) -> Employee:
    """Создаёт предприятие, должность и сотрудника через сервисы."""

    with storage.operation() as services:
        services.organization.set_organization(
            "Магазин", "1234567890", "123456789", "Адрес"
        )
        services.organization.set_position("Мастер", "2500", "0")
        employee = services.employees.add_employee(
            "Иван Иванов", "123456789012", "Мастер", date(2025, 1, 1), 0
        )
        services.calendar.set_norm(PERIOD, 22)
        services.timesheets.generate(PERIOD)
    return employee


def test_snapshot_and_restart(storage: SQLServiceProvider) -> None:
    """Новый провайдер читает данные, ведомость хранит старую карточку."""

    employee = prepare(storage)
    with storage.operation() as services:
        services.timesheets.fill(PERIOD, employee.employee_id, 20, 1, 1)
        services.payroll.calculate_period(PERIOD)
        services.employees.update_employee(
            employee.employee_id,
            "Новое ФИО",
            employee.inn,
            employee.position,
            employee.hire_date,
            1,
        )
        services.organization.set_organization(
            "Новое название", "1234567890", "123456789", "Адрес"
        )
    storage.engine.dispose()
    restarted = SQLServiceProvider(URL)
    try:
        with restarted.operation() as services:
            statement = services.payroll.get_statement(PERIOD)
            current = services.employees.get_employee_by_id(employee.employee_id)
        assert current.full_name == "Новое ФИО"
        assert statement.organization_name == "Магазин"
        assert statement.results[0].employee.full_name == "Иван Иванов"
        assert statement.total_to_pay == Decimal("43500.00")
    finally:
        restarted.engine.dispose()


def test_rollback_after_flush(storage: SQLServiceProvider) -> None:
    """Ошибка после записи откатывает изменения уже существующей ведомости."""

    employee = prepare(storage)
    with storage.operation() as services:
        services.timesheets.fill(PERIOD, employee.employee_id, 20, 1, 1)
        previous = services.payroll.calculate_period(PERIOD)
    with pytest.raises(RuntimeError, match="отказ"):
        with storage.operation() as services:
            services.timesheets.fill(PERIOD, employee.employee_id, 19, 2, 1)
            services.payroll.calculate_period(PERIOD, replace_existing=True)
            raise RuntimeError("отказ после flush")
    with storage.operation() as services:
        assert services.payroll.get_statement(PERIOD) == previous
        assert (
            services.timesheets.get(PERIOD).entries[employee.employee_id].worked_shifts
            == 20
        )
        assert services.payroll.is_current(PERIOD)


def test_relationships_and_cascades(storage: SQLServiceProvider) -> None:
    """Связь M:N доступна с обеих сторон, удаляются только зависимые строки."""

    employee = prepare(storage)
    with Session(storage.engine) as session, session.begin():
        row = session.get(EmployeeRow, employee.employee_id)
        assert row.position_row.name == "Мастер"
        sheet = row.timesheets[0]
        assert sheet.employees[0].employee_id == employee.employee_id
        assert sheet.entries[0].employee is row
        assert sheet.entries[0].worked_shifts is None
        session.delete(sheet)
    with Session(storage.engine) as session:
        assert session.scalar(select(func.count()).select_from(TimesheetEntryRow)) == 0
        assert session.get(EmployeeRow, employee.employee_id) is not None
    with storage.operation() as services:
        services.timesheets.generate(PERIOD)
        services.timesheets.fill(PERIOD, employee.employee_id, 0, 0, 0)
        services.payroll.calculate_period(PERIOD)
    with Session(storage.engine) as session, session.begin():
        sheet = session.scalar(select(TimesheetRow))
        session.delete(sheet.statement)
    with Session(storage.engine) as session:
        assert session.scalar(select(func.count()).select_from(StatementResultRow)) == 0
        assert session.get(EmployeeRow, employee.employee_id) is not None


def test_database_constraints(storage: SQLServiceProvider) -> None:
    """Сырые SQL-запросы не обходят CHECK и FK."""

    employee = prepare(storage)
    bad_queries = [
        (
            "UPDATE employees SET inn = 'bad' WHERE employee_id = :id",
            {"id": employee.employee_id},
        ),
        (
            "UPDATE employees SET dismissal_date = '2020-01-01' WHERE employee_id = :id",
            {"id": employee.employee_id},
        ),
        ("DELETE FROM employees WHERE employee_id = :id", {"id": employee.employee_id}),
        ("DELETE FROM positions WHERE name = 'Мастер'", {}),
        ("UPDATE organization SET id = 2", {}),
        ("UPDATE organization SET inn = '123456789012', kpp = '123456789'", {}),
    ]
    for query, parameters in bad_queries:
        with pytest.raises(IntegrityError), storage.engine.begin() as connection:
            connection.execute(text(query), parameters)
    foreign_keys = inspect(storage.engine).get_foreign_keys("statements")
    assert any(key["referred_table"] == "timesheets" for key in foreign_keys)


def test_norm_frozen_after_generation(storage: SQLServiceProvider) -> None:
    """Прямой вызов календаря тоже не меняет норму сформированного табеля."""

    prepare(storage)
    with pytest.raises(ValueError, match="норму"):
        with storage.operation() as services:
            services.calendar.set_norm(PERIOD, 20)
    with storage.operation() as services:
        assert services.calendar.get_norm(PERIOD) == 22
        assert services.timesheets.get(PERIOD).shift_norm == 22


def test_concurrent_generation(storage: SQLServiceProvider) -> None:
    """Две независимые транзакции создают один табель нового периода."""

    employee = prepare(storage)
    period = Period(2026, 10)
    barrier = Barrier(2)

    def generate() -> tuple[int, ...]:
        barrier.wait(timeout=5)
        with storage.operation() as services:
            return services.timesheets.generate(period).employee_ids

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: generate(), range(2)))
    assert results == [(employee.employee_id,), (employee.employee_id,)]
    with Session(storage.engine) as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(TimesheetRow)
                .where(TimesheetRow.month == 10)
            )
            == 1
        )


def test_sql_http_roundtrip(storage: SQLServiceProvider) -> None:
    """Веб сохраняет в PostgreSQL, новый экземпляр приложения читает запись."""

    app = create_web_application(provider=storage)
    with TestClient(app) as client:
        assert client.get("/api/state").status_code == 401
        assert (
            client.post(
                "/api/login", json={"username": "admin", "password": "admin"}
            ).status_code
            == 200
        )
        assert client.get("/").status_code == 200
        assert client.get("/assets/js/app.js").status_code == 200
        assert (
            client.put(
                "/api/organization",
                json={
                    "name": "Магазин",
                    "inn": "1234567890",
                    "kpp": "123456789",
                    "address": "Адрес",
                },
            ).status_code
            == 200
        )
        assert (
            client.put(
                "/api/positions",
                json={"name": "Мастер", "base_rate": "2500", "seniority_percent": "0"},
            ).status_code
            == 200
        )
        employee = {
            "full_name": "Иван Иванов",
            "inn": "123456789012",
            "position": "Мастер",
            "hire_date": "2025-01-01",
            "experience_years": 0,
        }
        response = client.post("/api/employees", json=employee)
        assert response.status_code == 201
        assert response.json()["rate_per_shift"] == "2500.00"
        identifier = response.json()["employee_id"]
        assert client.post("/api/employees", json=employee).status_code == 400
        path = "/api/periods/2026/9"
        assert client.put(path + "/norm", json={"shifts": 22}).status_code == 200
        assert client.post(path + "/timesheet").status_code == 200
        assert (
            client.put(
                path + f"/entries/{identifier}",
                json={"worked_shifts": 20, "sick_days": 1, "vacation_days": 1},
            ).status_code
            == 200
        )
        assert (
            client.post(path + "/statement", json={}).json()["statement"][
                "total_to_pay"
            ]
            == "43500.00"
        )
        assert client.post(path + "/close").status_code == 200
    with TestClient(create_web_application(provider=storage)) as client:
        client.post("/api/login", json={"username": "admin", "password": "admin"})
        assert len(client.get("/api/state").json()["employees"]) == 1
        assert client.get(path).json()["timesheet"]["closed"]


def test_concurrent_close_and_fill(storage: SQLServiceProvider) -> None:
    """Закрытый период не получает строку новее своей ведомости."""

    employee = prepare(storage)
    with storage.operation() as services:
        services.timesheets.fill(PERIOD, employee.employee_id, 20, 1, 1)
        services.payroll.calculate_period(PERIOD)
    barrier = Barrier(2)

    def operation(close: bool) -> bool:
        barrier.wait(timeout=5)
        try:
            with storage.operation() as services:
                if close:
                    services.payroll.close_period(PERIOD)
                else:
                    services.timesheets.fill(PERIOD, employee.employee_id, 21, 1, 0)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(operation, (True, False)))
    assert sum(outcomes) == 1
    with storage.operation() as services:
        sheet = services.timesheets.get(PERIOD)
        if sheet.closed:
            assert services.payroll.is_current(PERIOD)
            assert sheet.entries[employee.employee_id].worked_shifts == 20
        else:
            assert not services.payroll.is_current(PERIOD)
            assert sheet.entries[employee.employee_id].worked_shifts == 21


def test_metadata_matches_database_checks(storage: SQLServiceProvider) -> None:
    """Имена CHECK после миграции совпадают с декларативной схемой."""

    from sqlalchemy import CheckConstraint

    inspector = inspect(storage.engine)
    for table in Base.metadata.sorted_tables:
        expected = {
            storage.engine.dialect.identifier_preparer.format_constraint(item).strip(
                '"'
            )
            for item in table.constraints
            if isinstance(item, CheckConstraint)
        }
        actual = {item["name"] for item in inspector.get_check_constraints(table.name)}
        assert actual == expected


def test_sql_cli_reads_saved_employee(storage: SQLServiceProvider) -> None:
    """CLI использует ту же базу, что сервисы и веб."""

    from main import create_application
    from salary_calculator.cli.input_helpers import InputReader

    employee = prepare(storage)
    answers = iter(["admin", "admin", "6", "0"])
    messages = []
    reader = InputReader(
        input_function=lambda _: next(answers), output_function=messages.append
    )
    create_application(reader=reader, output=messages.append, provider=storage).run()
    output = "\n".join(messages)
    assert employee.full_name in output
    assert employee.inn in output
    assert "ошибка:" not in output


def test_supported_money_limit_fits_database(storage: SQLServiceProvider) -> None:
    """Максимальная ставка и надбавка помещаются без изменения копеек."""

    with storage.operation() as services:
        services.organization.set_organization(
            "Магазин", "1234567890", "123456789", "Адрес"
        )
        services.organization.set_position("Директор", "1000000000", "100")
        employee = services.employees.add_employee(
            "Иван Иванов", "123456789012", "Директор", date(2025, 1, 1), 80
        )
        assert employee.rate_per_shift == Decimal("81000000000.00")
        services.calendar.set_norm(PERIOD, 30)
        services.timesheets.generate(PERIOD)
        services.timesheets.fill(PERIOD, employee.employee_id, 30, 0, 0)
        statement = services.payroll.calculate_period(PERIOD)
        assert statement.total_accrued == Decimal("2430000000000.00")
    with storage.operation() as services:
        assert services.payroll.get_statement(PERIOD) == statement
