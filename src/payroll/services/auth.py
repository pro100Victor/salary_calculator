"""Учебная авторизация бухгалтера только на время работы CLI."""

from hashlib import pbkdf2_hmac
from hmac import compare_digest


class AuthService:
    """Проверяет демонстрационную учётную запись администратора."""

    def __init__(self) -> None:
        """Создаёт локальную учебную учётную запись admin/admin."""

        self._salt = b"salary-calculator-lab3-demo"
        self._password_hash = self._digest("admin")
        self._authenticated = False

    def _digest(self, password: str) -> bytes:
        """Вычисляет хэш для сравнения паролей."""

        return pbkdf2_hmac("sha256", password.encode(), self._salt, 10_000)

    def login(self, username: str, password: str) -> bool:
        """Разрешает доступ после проверки имени и пароля."""

        self._authenticated = username == "admin" and compare_digest(
            self._password_hash, self._digest(password)
        )
        return self._authenticated

    def logout(self) -> None:
        """Завершает сеанс бухгалтера."""

        self._authenticated = False

    def require_login(self) -> None:
        """Запрещает запуск операций без авторизации."""

        if not self._authenticated:
            raise PermissionError("сначала войдите в систему")
