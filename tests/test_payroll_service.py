"""Тесты расчёта заработной платы."""

import unittest

from salary_calculator.models import Employee
from salary_calculator.payroll_service import PayrollService


class PayrollServiceTest(unittest.TestCase):
    """Проверяет штатные и ошибочные варианты расчёта."""

    def setUp(self) -> None:
        """Создаёт сотрудника и сервис расчёта перед каждым тестом."""

        self.employee = Employee(
            employee_id=1,
            full_name="Иванов Иван Иванович",
            inn="123456789012",
            position="Продавец",
            rate_per_shift=2500.50,
        )
        self.service = PayrollService()

    def test_calculates_payroll_and_tax(self) -> None:
        """Рассчитывает начисление, НДФЛ 13 процентов и выплату."""

        result = self.service.calculate(
            employee=self.employee,
            worked_shifts=20,
            shift_norm=22,
        )

        self.assertEqual(result.accrued, 50010.00)
        self.assertEqual(result.tax, 6501.30)
        self.assertEqual(result.amount_to_pay, 43508.70)

    def test_calculates_zero_shifts(self) -> None:
        """Возвращает нулевые суммы при отсутствии отработанных смен."""

        result = self.service.calculate(
            employee=self.employee,
            worked_shifts=0,
            shift_norm=22,
        )

        self.assertEqual(result.accrued, 0)
        self.assertEqual(result.tax, 0)
        self.assertEqual(result.amount_to_pay, 0)

    def test_rejects_negative_shifts(self) -> None:
        """Отклоняет отрицательное количество смен."""

        with self.assertRaisesRegex(ValueError, "не может быть отрицательным"):
            self.service.calculate(
                employee=self.employee,
                worked_shifts=-1,
                shift_norm=22,
            )

    def test_rejects_shifts_above_norm(self) -> None:
        """Отклоняет количество смен больше установленной нормы."""

        with self.assertRaisesRegex(ValueError, "превышать норму"):
            self.service.calculate(
                employee=self.employee,
                worked_shifts=23,
                shift_norm=22,
            )


if __name__ == "__main__":
    unittest.main()
