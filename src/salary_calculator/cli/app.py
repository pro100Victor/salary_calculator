"""Главный класс консольного интерфейса."""

from collections.abc import Callable

from salary_calculator.cli.contracts import (
    EmployeeServiceProtocol,
    PayrollResultView,
    PayrollServiceProtocol,
)
from salary_calculator.cli.input_helpers import InputReader
from salary_calculator.cli.presenters import format_employee_list, format_payslip


class SalaryCalculatorCLI:
    """Организует взаимодействие пользователя с сервисами программы."""

    def __init__(
        self,
        employee_service: EmployeeServiceProtocol,
        payroll_service: PayrollServiceProtocol,
        input_reader: InputReader | None = None,
        output_function: Callable[[str], None] | None = None,
    ) -> None:
        """Получает необходимые сервисы и подготавливает состояние CLI."""

        self._employee_service = employee_service
        self._payroll_service = payroll_service
        self._output = output_function or print
        self._input_reader = input_reader or InputReader(
            output_function=self._output,
        )
        self._last_results: dict[int, PayrollResultView] = {}
        self._is_running = True

    def run(self) -> None:
        """Запускает главное меню и обрабатывает команды пользователя."""

        actions = {
            1: self._add_employee,
            2: self._show_employees,
            3: self._calculate_payroll,
            4: self._show_payslip,
            0: self._stop,
        }

        self._output("Salary Calculator")

        while self._is_running:
            self._show_menu()

            try:
                choice = self._input_reader.read_int(
                    "выберите действие: ",
                    minimum=0,
                    maximum=4,
                )
                actions[choice]()
            except (ValueError, LookupError) as error:
                self._output(f"ошибка: {error}")
            except (EOFError, KeyboardInterrupt):
                self._output("\nработа программы завершена")
                self._is_running = False

    def _show_menu(self) -> None:
        """Выводит доступные команды."""

        self._output(
            "\n1 - добавить сотрудника\n"
            "2 - показать сотрудников\n"
            "3 - рассчитать заработную плату\n"
            "4 - показать расчётный листок\n"
            "0 - завершить работу"
        )

    def _add_employee(self) -> None:
        """Запрашивает данные и передаёт их сервису сотрудников."""

        full_name = self._input_reader.read_non_empty("введите ФИО: ")
        inn = self._input_reader.read_non_empty("введите ИНН: ")
        position = self._input_reader.read_non_empty("введите должность: ")
        rate = self._input_reader.read_float(
            "введите ставку за смену: ",
            minimum=0.01,
        )

        employee = self._employee_service.add_employee(
            full_name=full_name,
            inn=inn,
            position=position,
            rate_per_shift=rate,
        )

        self._output(f"сотрудник добавлен, ID: {employee.employee_id}")

    def _show_employees(self) -> None:
        """Получает и выводит список сотрудников."""

        employees = self._employee_service.get_all_employees()
        self._output("\n" + format_employee_list(employees))

    def _calculate_payroll(self) -> None:
        """Запрашивает данные расчёта и выводит полученный листок."""

        employees = self._employee_service.get_all_employees()

        if not employees:
            self._output("сначала добавьте хотя бы одного сотрудника")
            return

        self._output("\n" + format_employee_list(employees))

        employee_id = self._input_reader.read_int(
            "введите ID сотрудника: ",
            minimum=1,
        )
        shift_norm = self._input_reader.read_int(
            "введите норму смен за месяц: ",
            minimum=1,
        )
        worked_shifts = self._input_reader.read_int(
            "введите количество отработанных смен: ",
            minimum=0,
        )

        employee = self._employee_service.get_employee_by_id(employee_id)
        result = self._payroll_service.calculate(
            employee=employee,
            worked_shifts=worked_shifts,
            shift_norm=shift_norm,
        )

        self._last_results[employee_id] = result
        self._output(format_payslip(result))

    def _show_payslip(self) -> None:
        """Повторно выводит последний расчётный листок сотрудника."""

        if not self._last_results:
            self._output("расчётные листки ещё не сформированы")
            return

        available_ids = ", ".join(
            str(employee_id) for employee_id in self._last_results
        )
        self._output(f"доступные ID сотрудников: {available_ids}")

        employee_id = self._input_reader.read_int(
            "введите ID сотрудника: ",
            minimum=1,
        )

        result = self._last_results.get(employee_id)

        if result is None:
            self._output("для этого сотрудника расчётный листок не найден")
            return

        self._output(format_payslip(result))

    def _stop(self) -> None:
        """Завершает цикл работы консольного приложения."""

        self._is_running = False
        self._output("работа программы завершена")
