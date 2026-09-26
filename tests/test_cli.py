"""Проверка компонентов консольного интерфейса."""

import unittest
from dataclasses import dataclass

from salary_calculator.cli.app import SalaryCalculatorCLI
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.cli.presenters import format_payslip


@dataclass
class FakeEmployee:
    """Тестовые данные сотрудника."""

    employee_id: int
    full_name: str
    inn: str
    position: str
    rate_per_shift: float


@dataclass
class FakePayrollResult:
    """Тестовые данные расчёта зарплаты."""

    employee: FakeEmployee
    worked_shifts: int
    accrued: float
    tax: float
    amount_to_pay: float


class FakeEmployeeService:
    """Имитирует сервис сотрудников при проверке CLI."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище сотрудников."""

        self.employees: list[FakeEmployee] = []

    def add_employee(
        self,
        full_name: str,
        inn: str,
        position: str,
        rate_per_shift: float,
    ) -> FakeEmployee:
        """Добавляет тестового сотрудника."""

        employee = FakeEmployee(
            employee_id=len(self.employees) + 1,
            full_name=full_name,
            inn=inn,
            position=position,
            rate_per_shift=rate_per_shift,
        )
        self.employees.append(employee)
        return employee

    def get_all_employees(self) -> list[FakeEmployee]:
        """Возвращает тестовых сотрудников."""

        return self.employees

    def get_employee_by_id(self, employee_id: int) -> FakeEmployee:
        """Ищет тестового сотрудника по идентификатору."""

        for employee in self.employees:
            if employee.employee_id == employee_id:
                return employee

        raise LookupError("сотрудник не найден")


class FakePayrollService:
    """Имитирует сервис расчёта при проверке CLI."""

    def calculate(
        self,
        employee: FakeEmployee,
        worked_shifts: int,
        shift_norm: int,
    ) -> FakePayrollResult:
        """Возвращает тестовый результат расчёта."""

        if worked_shifts > shift_norm:
            raise ValueError("количество смен превышает норму")

        accrued = employee.rate_per_shift * worked_shifts
        tax = accrued * 0.13

        return FakePayrollResult(
            employee=employee,
            worked_shifts=worked_shifts,
            accrued=accrued,
            tax=tax,
            amount_to_pay=accrued - tax,
        )


class InputReaderTest(unittest.TestCase):
    """Проверяет повторный запрос после неверного ввода."""

    def test_read_int_repeats_request(self) -> None:
        """Возвращает число после ошибочного строкового значения."""

        values = iter(["буквы", "7"])
        messages: list[str] = []
        reader = InputReader(
            input_function=lambda _: next(values),
            output_function=messages.append,
        )

        result = reader.read_int("число: ", minimum=0)

        self.assertEqual(result, 7)
        self.assertIn("ошибка: введите целое число", messages)


class PresenterTest(unittest.TestCase):
    """Проверяет текст расчётного листка."""

    def test_payslip_contains_calculation_result(self) -> None:
        """Выводит начисление, налог и сумму к выплате."""

        employee = FakeEmployee(1, "Иванов И. И.", "123456789012", "Продавец", 2500)
        result = FakePayrollResult(employee, 20, 50000, 6500, 43500)

        text = format_payslip(result)

        self.assertIn("Начислено: 50000.00 руб.", text)
        self.assertIn("НДФЛ 13%: 6500.00 руб.", text)
        self.assertIn("К выплате: 43500.00 руб.", text)


class ApplicationTest(unittest.TestCase):
    """Проверяет полный пользовательский сценарий CLI."""

    def test_add_employee_and_calculate_payroll(self) -> None:
        """Добавляет сотрудника и формирует расчётный листок."""

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
        reader = InputReader(
            input_function=lambda _: next(values),
            output_function=messages.append,
        )
        application = SalaryCalculatorCLI(
            employee_service=FakeEmployeeService(),
            payroll_service=FakePayrollService(),
            input_reader=reader,
            output_function=messages.append,
        )

        application.run()

        output = "\n".join(messages)
        self.assertIn("сотрудник добавлен, ID: 1", output)
        self.assertIn("К выплате: 43500.00 руб.", output)
        self.assertIn("работа программы завершена", output)


if __name__ == "__main__":
    unittest.main()
