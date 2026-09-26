"""Тесты сервиса сотрудников."""

import unittest

from salary_calculator.employee_service import EmployeeService


class EmployeeServiceTest(unittest.TestCase):
    """Проверяет добавление и получение сотрудников."""

    def setUp(self) -> None:
        """Создаёт пустой сервис перед каждым тестом."""

        self.service = EmployeeService()

    def test_add_employee(self) -> None:
        """Добавляет сотрудника с корректными данными."""

        employee = self.service.add_employee(
            full_name="Иванов Иван Иванович",
            inn="123456789012",
            position="Продавец",
            rate_per_shift=2500,
        )

        self.assertEqual(employee.employee_id, 1)
        self.assertEqual(employee.position, "Продавец")
        self.assertEqual(len(self.service.get_all_employees()), 1)

    def test_rejects_invalid_inn(self) -> None:
        """Отклоняет ИНН, который не состоит из 12 цифр."""

        with self.assertRaisesRegex(ValueError, "12 цифр"):
            self.service.add_employee(
                full_name="Иванов Иван Иванович",
                inn="123ABC",
                position="Продавец",
                rate_per_shift=2500,
            )

    def test_rejects_duplicate_inn(self) -> None:
        """Не позволяет добавить двух сотрудников с одинаковым ИНН."""

        self.service.add_employee(
            full_name="Иванов Иван Иванович",
            inn="123456789012",
            position="Продавец",
            rate_per_shift=2500,
        )

        with self.assertRaisesRegex(ValueError, "уже существует"):
            self.service.add_employee(
                full_name="Петров Пётр Петрович",
                inn="123456789012",
                position="Менеджер",
                rate_per_shift=3000,
            )

    def test_rejects_negative_rate(self) -> None:
        """Отклоняет отрицательную ставку за смену."""

        with self.assertRaisesRegex(ValueError, "больше нуля"):
            self.service.add_employee(
                full_name="Иванов Иван Иванович",
                inn="123456789012",
                position="Продавец",
                rate_per_shift=-1,
            )

    def test_raises_error_for_unknown_employee(self) -> None:
        """Сообщает об отсутствии сотрудника с указанным ID."""

        with self.assertRaisesRegex(LookupError, "не найден"):
            self.service.get_employee_by_id(10)


if __name__ == "__main__":
    unittest.main()
