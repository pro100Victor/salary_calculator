"""Интеграционный тест полного сценария в терминале."""

import unittest
from decimal import Decimal

from main import create_application
from salary_calculator.cli.input_helpers import InputReader


class CLITest(unittest.TestCase):
    """Проверяет действительную сборку CLI со всеми сервисами."""

    def test_complete_user_scenario(self) -> None:
        """От авторизации проходит до закрытия периода и расчётного листка."""

        answers = iter(
            [
                "admin",
                "admin",
                "1",
                "Магазин",
                "1234567890",
                "123456789",
                "Волгоград",
                "2",
                "Продавец",
                "2500",
                "0",
                "3",
                "Иванов Иван Иванович",
                "123456789012",
                "Продавец",
                "01.01.2026",
                "0",
                "7",
                "2026",
                "9",
                "22",
                "8",
                "2026",
                "9",
                "9",
                "2026",
                "9",
                "1",
                "20",
                "1",
                "1",
                "10",
                "2026",
                "9",
                "11",
                "2026",
                "9",
                "12",
                "2026",
                "9",
                "1",
                "13",
                "2026",
                "9",
                "да",
                "9",
                "2026",
                "9",
                "1",
                "0",
                "0",
                "0",
                "0",
            ]
        )
        messages: list[str] = []
        reader = InputReader(
            input_function=lambda _: next(answers),
            output_function=messages.append,
        )
        application = create_application(reader=reader, output=messages.append)
        application.run()

        output = "\n".join(messages)
        self.assertIn("сотрудник добавлен, ID: 1", output)
        self.assertIn("ИТОГО: начислено 50000.00", output)
        self.assertIn("НДФЛ 13%: 6500.00 руб.", output)
        self.assertIn("период 09.2026 закрыт", output)
        self.assertIn("ошибка: расчётный период закрыт", output)
        self.assertIn("работа программы завершена", output)

    def test_bad_login_rejects_menu(self) -> None:
        """Три неверных пароля не открывают бухгалтерское меню."""

        answers = iter(["admin", "bad", "admin", "bad", "admin", "bad"])
        messages: list[str] = []
        reader = InputReader(
            input_function=lambda _: next(answers),
            output_function=messages.append,
        )
        application = create_application(reader=reader, output=messages.append)
        application.run()
        self.assertEqual("\n".join(messages).count("неверный логин"), 3)
        self.assertNotIn("вход выполнен", messages)

    def test_reader_retries_after_letters_in_number(self) -> None:
        """Буквы вместо смен не прерывают ввод."""

        answers = iter(["два", "2", "NaN", "2,50"])
        messages: list[str] = []
        reader = InputReader(
            input_function=lambda _: next(answers), output_function=messages.append
        )
        self.assertEqual(reader.read_int("смены: ", 0), 2)
        self.assertEqual(reader.read_decimal("ставка: "), Decimal("2.50"))
        self.assertEqual(len(messages), 2)


if __name__ == "__main__":
    unittest.main()
