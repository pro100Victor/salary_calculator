"""Отдельные учебные веб-сеансы, не связанные с глобальным флагом CLI."""

from secrets import token_urlsafe
from threading import RLock
from time import monotonic

from salary_calculator.services.auth import AuthService


class SessionStore:
    """Хранит случайные токены одного локального процесса в течение часа."""

    def __init__(self) -> None:
        """Создаёт пустое хранилище сеансов."""

        self._tokens: dict[str, float] = {}
        self._lock = RLock()

    def login(self, username: str, password: str) -> str:
        """Проверяет существующую учебную учётную запись и выдаёт новый токен."""

        if not AuthService().login(username, password):
            raise PermissionError("неверный логин или пароль")
        with self._lock:
            now = monotonic()
            self._tokens = {key: end for key, end in self._tokens.items() if end > now}
            token = token_urlsafe(32)
            self._tokens[token] = now + 3600
            return token

    def require(self, token: str) -> None:
        """Запрещает доступ без действующего веб-сеанса."""

        with self._lock:
            if self._tokens.get(token, 0) <= monotonic():
                self._tokens.pop(token, None)
                raise PermissionError("войдите в систему")

    def logout(self, token: str) -> None:
        """Удаляет только сеанс текущего браузера."""

        with self._lock:
            self._tokens.pop(token, None)
