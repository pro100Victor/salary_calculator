"""Формирование текста для вывода в терминал."""

from collections.abc import Sequence

from salary_calculator.cli.contracts import EmployeeView, PayrollResultView


def format_employee(employee: EmployeeView) -> str:
    """Формирует текст с данными одного сотрудника."""

    return (
        f"ID: {employee.employee_id}\n"
        f"ФИО: {employee.full_name}\n"
        f"ИНН: {employee.inn}\n"
        f"Должность: {employee.position}\n"
        f"Ставка за смену: {employee.rate_per_shift:.2f} руб."
    )


def format_employee_list(employees: Sequence[EmployeeView]) -> str:
    """Формирует список сотрудников для вывода в терминал."""

    if not employees:
        return "список сотрудников пуст"

    separator = "\n" + "-" * 50 + "\n"
    return separator.join(format_employee(employee) for employee in employees)


def format_payslip(result: PayrollResultView) -> str:
    """Формирует расчётный листок сотрудника."""

    employee = result.employee

    return (
        "\nРАСЧЁТНЫЙ ЛИСТОК\n"
        f"Сотрудник: {employee.full_name}\n"
        f"Должность: {employee.position}\n"
        f"Ставка за смену: {employee.rate_per_shift:.2f} руб.\n"
        f"Отработано смен: {result.worked_shifts}\n\n"
        f"Начислено: {result.accrued:.2f} руб.\n"
        f"НДФЛ 13%: {result.tax:.2f} руб.\n"
        f"К выплате: {result.amount_to_pay:.2f} руб."
    )
