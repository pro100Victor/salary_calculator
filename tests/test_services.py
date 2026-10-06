"""Проверки организации, кадров, табеля и начисления без внешних библиотек."""

import unittest
from abc import ABC
from datetime import date
from decimal import Decimal

from salary_calculator.calendar_service import CalendarService
from salary_calculator.contracts import (
    EmployeeRepository,
    SalaryCalculationStrategy,
    StatementRepository,
    TimesheetRepository,
)
from salary_calculator.employee_service import EmployeeService
from salary_calculator.models import Period
from salary_calculator.organization_service import OrganizationService
from salary_calculator.payroll_service import PayrollService
from salary_calculator.repositories import (
    InMemoryEmployeeRepository,
    InMemoryStatementRepository,
    InMemoryTimesheetRepository,
)
from salary_calculator.timesheet_service import TimesheetService


class IncompleteStrategy(SalaryCalculationStrategy):
    """Показывает ошибку создания класса без абстрактного метода."""


class FailingStrategy(SalaryCalculationStrategy):
    """Имитирует отказ расчёта для проверки сохранности прежней ведомости."""

    def calculate(self, rate_per_shift: Decimal, worked_shifts: int) -> Decimal:
        """Отказывает в расчёте любого начисления."""

        raise ValueError("ошибка тестовой стратегии")


class ServiceTest(unittest.TestCase):
    """Проверяет нормальную и ошибочную работу предметных сервисов."""

    def setUp(self) -> None:
        """Подготавливает одно предприятие и связанные InMemory-сервисы."""

        self.organization = OrganizationService()
        self.organization.set_organization(
            "Магазин", "1234567890", "123456789", "Волгоград"
        )
        self.organization.set_position("Продавец", "2500.00", "5")
        self.employee_repo = InMemoryEmployeeRepository()
        self.employees = EmployeeService(self.employee_repo, self.organization)
        self.calendar = CalendarService()
        self.timesheet_repo = InMemoryTimesheetRepository()
        self.timesheets = TimesheetService(
            self.timesheet_repo, self.employees, self.calendar
        )
        self.statement_repo = InMemoryStatementRepository()
        self.payroll = PayrollService(
            self.statement_repo, self.timesheets, self.employees, self.organization
        )
        self.period = Period(2026, 9)
        self.employee = self.employees.add_employee(
            "Иванов Иван Иванович", "123456789012", "Продавец", date(2026, 1, 10), 2
        )

    def test_abstract_classes_reject_incomplete_child(self) -> None:
        """Проверяет замечание преподавателя о явных ABC-интерфейсах."""

        self.assertTrue(issubclass(SalaryCalculationStrategy, ABC))
        self.assertTrue(issubclass(InMemoryEmployeeRepository, EmployeeRepository))
        self.assertTrue(issubclass(InMemoryTimesheetRepository, TimesheetRepository))
        self.assertTrue(issubclass(InMemoryStatementRepository, StatementRepository))
        with self.assertRaises(TypeError):
            IncompleteStrategy()

    def test_rate_depends_on_position_and_seniority(self) -> None:
        """Добавляет надбавку в размере двух полных годов по 5%."""

        self.assertEqual(self.employee.rate_per_shift, Decimal("2750.00"))

    def test_employee_validation_and_dismissal(self) -> None:
        """Отклоняет дубликат и исключает уволенного из будущих периодов."""

        with self.assertRaisesRegex(ValueError, "уже существует"):
            self.employees.add_employee(
                "Другое ФИО", self.employee.inn, "Продавец", date(2026, 1, 10), 0
            )
        dismissed = self.employees.dismiss_employee(
            self.employee.employee_id, date(2026, 9, 15)
        )
        self.assertEqual(dismissed.status, "Уволен")
        self.assertEqual(len(self.employees.employed_in(self.period)), 1)
        self.assertEqual(self.employees.employed_in(Period(2026, 10)), [])

    def test_employee_edit_recalculates_rate(self) -> None:
        """Перевод на новую должность применяет новый тариф и стаж."""

        self.organization.set_position("Управляющий", "4000.00", "0")
        updated = self.employees.update_employee(
            self.employee.employee_id,
            "Иванов Иван Иванович",
            self.employee.inn,
            "Управляющий",
            date(2026, 1, 10),
            2,
        )
        self.assertEqual(updated.rate_per_shift, Decimal("4000.00"))
        self.assertEqual(self.employees.get_employee_by_id(1), updated)

    def test_bad_organization_and_rate(self) -> None:
        """Проверяет ИНН организации, неверный стаж и переполненную ставку."""

        with self.assertRaisesRegex(ValueError, "ИНН организации"):
            self.organization.set_organization("Магазин", "ABC", "", "Адрес")
        with self.assertRaisesRegex(ValueError, "стаж"):
            self.organization.rate_for("Продавец", -1)
        with self.assertRaisesRegex(ValueError, "слишком велика"):
            self.organization.set_position("Директор", "1e100", 0)

    def test_timesheet_reuses_period_and_validates_days(self) -> None:
        """Не создаёт дубликат и не сохраняет превышение нормы."""

        self.calendar.set_norm(self.period, 22)
        first = self.timesheets.generate(self.period)
        self.assertIs(first, self.timesheets.generate(self.period))
        with self.assertRaisesRegex(ValueError, "превышает норму"):
            self.timesheets.fill(self.period, self.employee.employee_id, 21, 1, 1)
        self.assertEqual(first.entries, {})
        self.timesheets.fill(self.period, self.employee.employee_id, 20, 1, 1)
        self.assertEqual(first.revision, 1)

    def test_payroll_statement_and_payslip(self) -> None:
        """Считает НДФЛ и сохраняет итог предприятия для одного работника."""

        self.calendar.set_norm(self.period, 22)
        self.timesheets.generate(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 20, 1, 1)
        statement = self.payroll.calculate_period(self.period)
        result = self.payroll.get_payslip(self.period, self.employee.employee_id)
        self.assertEqual(result.accrued, Decimal("55000.00"))
        self.assertEqual(result.tax, Decimal("7150.00"))
        self.assertEqual(statement.total_to_pay, Decimal("47850.00"))
        self.assertTrue(self.payroll.is_current(self.period))

    def test_missing_row_and_invalid_numbers(self) -> None:
        """Не рассчитывает незаполненные и отрицательные строки."""

        self.timesheets.generate(self.period)
        with self.assertRaisesRegex(ValueError, "не заполнены"):
            self.payroll.calculate_period(self.period)
        with self.assertRaisesRegex(ValueError, "отрицательными"):
            self.timesheets.fill(self.period, self.employee.employee_id, -1, 0, 0)
        with self.assertRaisesRegex(ValueError, "целыми"):
            self.timesheets.fill(self.period, self.employee.employee_id, 1.5, 0, 0)

    def test_previous_statement_survives_failure(self) -> None:
        """Ошибка повторного расчёта не заменяет прошлый результат."""

        self.timesheets.generate(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 10, 0, 0)
        previous = self.payroll.calculate_period(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 11, 0, 0)
        self.assertFalse(self.payroll.is_current(self.period))
        failing = PayrollService(
            self.statement_repo,
            self.timesheets,
            self.employees,
            self.organization,
            FailingStrategy(),
        )
        with self.assertRaisesRegex(ValueError, "ошибка тестовой стратегии"):
            failing.calculate_period(self.period, replace_existing=True)
        self.assertIs(self.payroll.get_statement(self.period), previous)

    def test_two_employees_contribute_to_totals(self) -> None:
        """Итог ведомости равен сумме двух персональных расчётов."""

        second = self.employees.add_employee(
            "Петров Пётр Петрович", "987654321098", "Продавец", date(2026, 2, 1), 0
        )
        self.timesheets.generate(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 10, 0, 0)
        self.timesheets.fill(self.period, second.employee_id, 10, 0, 0)
        statement = self.payroll.calculate_period(self.period)
        self.assertEqual(len(statement.results), 2)
        self.assertEqual(statement.total_accrued, Decimal("52500.00"))
        self.assertEqual(statement.total_tax, Decimal("6825.00"))
        self.assertEqual(statement.total_to_pay, Decimal("45675.00"))

    def test_closed_period_rejects_mutations(self) -> None:
        """После закрытия нельзя вводить смены и пересчитывать ведомость."""

        self.timesheets.generate(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 0, 0, 0)
        self.payroll.calculate_period(self.period)
        self.payroll.close_period(self.period)
        with self.assertRaisesRegex(ValueError, "закрыт"):
            self.timesheets.fill(self.period, self.employee.employee_id, 1, 0, 0)
        with self.assertRaisesRegex(ValueError, "закрытый"):
            self.payroll.calculate_period(self.period, replace_existing=True)

    def test_zero_shifts_and_rounding(self) -> None:
        """Нулевые смены дают нулевую выплату и корректный налог."""

        self.timesheets.generate(self.period)
        self.timesheets.fill(self.period, self.employee.employee_id, 0, 0, 0)
        result = self.payroll.calculate_period(self.period).results[0]
        self.assertEqual(result.amount_to_pay, Decimal("0.00"))

    def test_default_calendar_is_weekdays(self) -> None:
        """Автоматическая норма считает будни без праздников."""

        self.assertEqual(self.calendar.get_norm(Period(2026, 9)), 22)


if __name__ == "__main__":
    unittest.main()
