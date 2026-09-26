"""Интеграционные тесты общей работы компонентов проекта."""

import unittest

from salary_calculator.cli import SalaryCalculatorCLI
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.employee_service import EmployeeService
from salary_calculator.payroll_service import PayrollService


class ProjectIntegrationTest(unittest.TestCase):
    """Проверяет соединение интерфейса, хранилища и расчётного ядра."""

    def test_services_complete_payroll_scenario(self) -> None:
        """Добавляет сотрудника и рассчитывает его зарплату."""

        employee_service = EmployeeService()
        payroll_service = PayrollService()

        employee = employee_service.add_employee(
            full_name="Иванов Иван Иванович",
            inn="123456789012",
            position="Продавец",
            rate_per_shift=2500,
        )
        result = payroll_service.calculate(
            employee=employee,
            worked_shifts=20,
            shift_norm=22,
        )

        self.assertEqual(result.accrued, 50000)
        self.assertEqual(result.tax, 6500)
        self.assertEqual(result.amount_to_pay, 43500)

    def test_cli_works_with_real_services(self) -> None:
        """Выполняет полный пользовательский сценарий через настоящее CLI."""

        values = iter(
            [
                "1",
                "Иванов Иван Иванович",
                "123456789012",
                "Продавец",
                "2500",
                "3",
                "1",
                "22",
                "20",
                "0",
            ]
        )
        messages: list[str] = []
        input_reader = InputReader(
            input_function=lambda _: next(values),
            output_function=messages.append,
        )
        application = SalaryCalculatorCLI(
            employee_service=EmployeeService(),
            payroll_service=PayrollService(),
            input_reader=input_reader,
            output_function=messages.append,
        )

        application.run()

        output = "\n".join(messages)
        self.assertIn("сотрудник добавлен, ID: 1", output)
        self.assertIn("Начислено: 50000.00 руб.", output)
        self.assertIn("НДФЛ 13%: 6500.00 руб.", output)
        self.assertIn("К выплате: 43500.00 руб.", output)


if __name__ == "__main__":
    unittest.main()
