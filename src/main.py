"""Единая точка входа в программу Salary Calculator."""

from salary_calculator.cli import SalaryCalculatorCLI
from salary_calculator.employee_service import EmployeeService
from salary_calculator.payroll_service import PayrollService


def create_application() -> SalaryCalculatorCLI:
    """Создаёт сервисы и связывает их с консольным интерфейсом."""

    employee_service = EmployeeService()
    payroll_service = PayrollService()

    return SalaryCalculatorCLI(
        employee_service=employee_service,
        payroll_service=payroll_service,
    )


def main() -> None:
    """Запускает консольное приложение."""

    application = create_application()
    application.run()


if __name__ == "__main__":
    main()
