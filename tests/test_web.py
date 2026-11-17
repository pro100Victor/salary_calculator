"""Проверки HTTP-границы и отдельных пользовательских сеансов."""

import unittest
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from salary_calculator.application.errors import StorageError
from salary_calculator.application.memory_provider import InMemoryServiceProvider
from salary_calculator.application.services import ApplicationServices
from salary_calculator.web.app import create_web_application


class WebTest(unittest.TestCase):
    """Проверяет реальные сервисы через HTTP без PostgreSQL."""

    def setUp(self) -> None:
        """Открывает чистое приложение и учебный сеанс."""

        self.app = create_web_application()
        self.client = TestClient(self.app)
        self.client.post("/api/login", json={"username": "admin", "password": "admin"})

    def prepare_employee(self) -> None:
        """Создаёт исходные данные штатными HTTP-командами."""

        self.client.put(
            "/api/organization",
            json={
                "name": "Магазин",
                "inn": "1234567890",
                "kpp": "123456789",
                "address": "Волгоград",
            },
        ).raise_for_status()
        self.client.put(
            "/api/positions",
            json={
                "name": "Продавец",
                "base_rate": "2500.00",
                "seniority_percent": "0",
            },
        ).raise_for_status()
        self.employee = {
            "full_name": "Иванов Иван Иванович",
            "inn": "123456789012",
            "position": "Продавец",
            "hire_date": "2026-01-01",
            "experience_years": 0,
        }
        self.assertEqual(
            self.client.post("/api/employees", json=self.employee).status_code, 201
        )

    def test_full_payroll_and_recovery(self) -> None:
        """Ошибочный ввод не мешает повтору, расчёту и закрытию."""

        self.prepare_employee()
        path = "/api/periods/2026/9"
        self.client.put(path + "/norm", json={"shifts": 22}).raise_for_status()
        self.client.post(path + "/timesheet").raise_for_status()
        for bad in (-1, "буквы", 23):
            response = self.client.put(
                path + "/entries/1",
                json={
                    "worked_shifts": bad,
                    "sick_days": 0,
                    "vacation_days": 0,
                },
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("worked_shifts", response.json()["fields"])
        row = {"worked_shifts": 20, "sick_days": 1, "vacation_days": 1}
        self.client.put(path + "/entries/1", json=row).raise_for_status()
        response = self.client.post(path + "/statement", json={})
        self.assertEqual(response.json()["statement"]["total_to_pay"], "43500.00")
        row.update(worked_shifts=19, sick_days=2)
        self.client.put(path + "/entries/1", json=row).raise_for_status()
        self.assertFalse(self.client.get(path).json()["statement"]["is_current"])
        self.assertEqual(self.client.post(path + "/close").status_code, 400)
        self.assertEqual(
            self.client.post(path + "/statement", json={}).status_code, 400
        )
        self.client.post(
            path + "/statement", json={"replace_existing": True}
        ).raise_for_status()
        self.client.post(path + "/close").raise_for_status()
        self.assertEqual(
            self.client.put(path + "/entries/1", json=row).status_code, 400
        )

    def test_duplicate_and_date_order(self) -> None:
        """Ошибки ИНН и увольнения указывают на соответствующее поле."""

        self.prepare_employee()
        response = self.client.post("/api/employees", json=self.employee)
        self.assertEqual(response.status_code, 400)
        self.assertIn("inn", response.json()["fields"])
        response = self.client.post(
            "/api/employees/1/dismiss", json={"dismissal_date": "2025-12-31"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("dismissal_date", response.json()["fields"])

    def test_separate_sessions(self) -> None:
        """Вход одного браузера не разрешает доступ другому."""

        self.assertEqual(TestClient(self.app).get("/api/state").status_code, 401)
        self.assertEqual(self.client.get("/api/state").status_code, 200)
        self.client.post("/api/logout")
        self.assertEqual(self.client.get("/api/state").status_code, 401)

    def test_storage_error_and_retry(self) -> None:
        """Отказ хранилища даёт безопасный 503, следующий запрос работает."""

        original = self.app.state.provider

        class BrokenProvider(InMemoryServiceProvider):
            """Имитирует отказ будущей БД."""

            @contextmanager
            def operation(self) -> Iterator[ApplicationServices]:
                """Имитирует отказ commit после работы обработчика."""

                with super().operation() as services:
                    yield services
                    raise StorageError("secret connection string")

        self.app.state.provider = BrokenProvider()
        response = self.client.get("/api/state")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)
        self.app.state.provider = original
        self.assertEqual(self.client.get("/api/state").status_code, 200)

    def test_static_and_empty_period(self) -> None:
        """Чтение пустого периода не создаёт табель."""

        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/assets/js/app.js").status_code, 200)
        data = self.client.get("/api/periods/2026/9").json()
        self.assertIsNone(data["timesheet"])
        self.assertIsNone(data["statement"])
        self.assertEqual(self.client.get("/api/periods/2026/13").status_code, 400)
