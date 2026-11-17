"""Реальные SQL-запросы, восстановление объектов и откат через новые Session."""

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.operations.ops import OpContainer
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers, sessionmaker
from sqlalchemy.schema import CreateTable

from main import create_application
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.db.base import Base
from salary_calculator.db.models import (
    EmployeeRow,
    OrganizationRow,
    PayrollResultRow,
    TimesheetRow,
)
from salary_calculator.models import Period
from salary_calculator.web.app import create_web_application
from tests.support.sql_provider import TestSQLProvider


class SQLBackendTest(unittest.TestCase):
    """Проверяет SQL-адаптер; PostgreSQL-блокировки проверяет инженер 3 отдельно."""

    def setUp(self) -> None:
        """Создаёт схему только операциями Alembic на временной SQLite-БД."""
        self.directory = tempfile.TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.directory.name) / 'salary.db'}"
        self.engine = create_engine(self.url)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, record) -> None:
            """Включает реальную проверку внешних ключей SQLite."""
            connection.execute("PRAGMA foreign_keys=ON")

        configure_mappers()
        with self.engine.begin() as connection:
            context = MigrationContext.configure(connection)
            migration = produce_migrations(context, Base.metadata)
            operations = Operations(context)

            def apply(container: OpContainer) -> None:
                """Выполняет сгенерированные операции, включая индексы."""
                for operation in container.ops:
                    if isinstance(operation, OpContainer):
                        apply(operation)
                    else:
                        operations.invoke(operation)

            apply(migration.upgrade_ops)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        self.provider = TestSQLProvider(self.sessions)
        self.period = Period(2026, 9)

    def tearDown(self) -> None:
        """Удаляет только временную тестовую БД."""
        self.engine.dispose()
        self.directory.cleanup()

    def seed(self) -> int:
        """Сохраняет базовые данные через сервисы в одной операции."""
        with self.provider.operation() as services:
            services.organization.set_organization(
                "Магазин", "0123456789", "012345678", "Волгоград"
            )
            services.organization.set_position("Продавец", "2500", "0")
            employee = services.employees.add_employee(
                "Иванов Иван Иванович", "012345678901", "Продавец", date(2026, 1, 1), 0
            )
            services.calendar.set_norm(self.period, 22)
        return employee.employee_id

    def test_persistence_in_new_sessions_and_engine(self) -> None:
        """Сохраняет все данные и закрытие после повторного подключения к файлу."""
        employee_id = self.seed()
        with self.provider.operation() as services:
            sheet = services.timesheets.generate(self.period)
            self.assertNotIn(employee_id, sheet.entries)
        with self.provider.operation() as services:
            self.assertNotIn(employee_id, services.timesheets.get(self.period).entries)
            services.timesheets.fill(self.period, employee_id, 20, 1, 1)
        with self.provider.operation() as services:
            statement = services.payroll.calculate_period(self.period)
            self.assertEqual(statement.total_to_pay, Decimal("43500.00"))
            services.payroll.close_period(self.period)
        self.engine.dispose()
        other = create_engine(self.url)
        try:
            with other.connect() as connection:
                connection.execute(text("PRAGMA foreign_keys=ON"))
            sessions = sessionmaker(other, expire_on_commit=False)
            with TestSQLProvider(sessions).operation() as services:
                self.assertEqual(
                    services.organization.get_organization().inn, "0123456789"
                )
                self.assertEqual(
                    services.organization.get_position("пРОДАВЕЦ").base_rate,
                    Decimal("2500"),
                )
                self.assertEqual(services.calendar.get_norm(self.period), 22)
                self.assertTrue(services.timesheets.get(self.period).closed)
                self.assertEqual(
                    services.payroll.get_statement(self.period).total_tax,
                    Decimal("6500.00"),
                )
                with self.assertRaises(ValueError):
                    services.timesheets.fill(self.period, employee_id, 0, 0, 0)
        finally:
            other.dispose()

    def test_snapshot_and_mapping_after_session_closed(self) -> None:
        """Снимок листка не меняется после изменения карточки и реквизитов."""
        employee_id = self.seed()
        with self.provider.operation() as services:
            services.timesheets.generate(self.period)
            services.timesheets.fill(self.period, employee_id, 20, 1, 1)
            services.payroll.calculate_period(self.period)
        with self.provider.operation() as services:
            services.organization.set_position("Мастер", "3000", "0")
            services.employees.update_employee(
                employee_id, "Новое ФИО", "012345678901", "Мастер", date(2026, 1, 1), 1
            )
            services.organization.set_organization(
                "Новое предприятие", "0123456789", "012345678", "Другой адрес"
            )
        with self.provider.operation() as services:
            old = services.payroll.get_statement(self.period)
            current = services.employees.get_employee_by_id(employee_id)
        self.assertEqual(old.results[0].employee.full_name, "Иванов Иван Иванович")
        self.assertEqual(old.results[0].employee.position, "Продавец")
        self.assertEqual(old.organization_name, "Магазин")
        self.assertEqual(old.total_to_pay, Decimal("43500.00"))
        self.assertEqual(current.full_name, "Новое ФИО")

    def test_atomic_rollback_and_recalculation(self) -> None:
        """Сбой после SQL flush не уничтожает прежнюю ведомость."""
        employee_id = self.seed()
        with self.provider.operation() as services:
            services.timesheets.generate(self.period)
            services.timesheets.fill(self.period, employee_id, 20, 1, 1)
            services.payroll.calculate_period(self.period)
        with self.provider.operation() as services:
            services.timesheets.fill(self.period, employee_id, 19, 2, 1)
        with self.assertRaises(ValueError):
            with self.provider.operation() as services:
                services.payroll.calculate_period(self.period, True)
                raise ValueError("имитация сбоя после записи")
        with self.provider.operation() as services:
            self.assertEqual(
                services.payroll.get_statement(self.period).total_to_pay,
                Decimal("43500.00"),
            )
            self.assertFalse(services.payroll.is_current(self.period))
            statement = services.payroll.calculate_period(self.period, True)
            self.assertEqual(statement.total_to_pay, Decimal("41325.00"))
        with self.sessions() as session:
            self.assertEqual(len(session.scalars(select(PayrollResultRow)).all()), 1)

    def test_zero_and_absence_and_many_to_many(self) -> None:
        """Нули сохраняются как заполненная строка; many-to-many читает состав."""
        employee_id = self.seed()
        with self.provider.operation() as services:
            services.timesheets.generate(self.period)
            services.timesheets.fill(self.period, employee_id, 0, 0, 0)
        with self.provider.operation() as services:
            sheet = services.timesheets.get(self.period)
            self.assertEqual(sheet.entries[employee_id].worked_shifts, 0)
            with self.assertRaises(ValueError):
                services.calendar.set_norm(self.period, 20)
            with self.assertRaises(ValueError):
                services.timesheets.fill(self.period, employee_id, 23, 0, 0)
        with self.sessions() as session:
            employee = session.get(EmployeeRow, employee_id)
            sheet = session.scalar(select(TimesheetRow))
            self.assertEqual([item.id for item in sheet.employees], [employee_id])
            self.assertEqual([item.id for item in employee.timesheets], [sheet.id])

    def test_database_constraints(self) -> None:
        """Ограничения БД действуют и при обходе сервисов, FK не удаляет историю."""
        employee_id = self.seed()
        with self.provider.operation() as services:
            services.timesheets.generate(self.period)
        for sql in (
            "UPDATE employees SET inn='abcdefghijkl'",
            "UPDATE employees SET experience_years=-1",
            "UPDATE employees SET dismissal_date='2025-01-01'",
            "UPDATE positions SET base_rate=-1",
            "UPDATE timesheet_entries SET worked_shifts=1",
            f"DELETE FROM employees WHERE id={employee_id}",
        ):
            with self.assertRaises(IntegrityError):
                with self.sessions.begin() as session:
                    session.execute(text(sql))
        with self.sessions.begin() as session:
            row = session.get(EmployeeRow, employee_id)
            self.assertEqual(row.inn, "012345678901")
        self.assertEqual(OrganizationRow.__table__.primary_key.columns.keys(), ["id"])

    def test_http_uses_sql_without_frontend_changes(self) -> None:
        """HTTP-контракт сохраняется при подстановке SQL-провайдера."""
        self.seed()
        client = TestClient(create_web_application(self.provider))
        client.post("/api/login", json={"username": "admin", "password": "admin"})
        data = client.get("/api/state").json()
        self.assertEqual(data["employees"][0]["rate_per_shift"], "2500.00")
        path = "/api/periods/2026/9"
        client.post(path + "/timesheet").raise_for_status()
        response = client.put(
            path + "/entries/1",
            json={"worked_shifts": 23, "sick_days": 0, "vacation_days": 0},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("worked_shifts", response.json()["fields"])
        client.put(
            path + "/entries/1",
            json={"worked_shifts": 20, "sick_days": 1, "vacation_days": 1},
        ).raise_for_status()
        self.assertEqual(
            client.post(path + "/statement", json={}).json()["statement"][
                "total_to_pay"
            ],
            "43500.00",
        )
        another = TestClient(create_web_application(TestSQLProvider(self.sessions)))
        another.post("/api/login", json={"username": "admin", "password": "admin"})
        self.assertEqual(
            another.get(path).json()["statement"]["total_to_pay"], "43500.00"
        )

    def test_cli_accepts_sql_provider(self) -> None:
        """Старый CLI читает SQL-данные через ту же точку сборки."""
        self.seed()
        answers = iter(["admin", "admin", "6", "0"])
        output: list[str] = []
        reader = InputReader(
            input_function=lambda _: next(answers), output_function=output.append
        )
        create_application(
            reader=reader, output=output.append, provider=self.provider
        ).run()
        self.assertIn("Иванов Иван Иванович", "\n".join(output))

    def test_postgresql_ddl_compiles(self) -> None:
        """Проверяет PostgreSQL-DDL; не заменяет выполнение на сервере PostgreSQL."""
        for table in Base.metadata.sorted_tables:
            ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
            self.assertIn("PRIMARY KEY", ddl)
        self.assertIn(
            "NUMERIC(20, 2)",
            str(
                CreateTable(EmployeeRow.__table__).compile(dialect=postgresql.dialect())
            ),
        )
