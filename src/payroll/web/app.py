"""Сборка веб-приложения, обработка ошибок и выдача frontend-файлов."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from payroll.application.errors import StorageError
from payroll.application.factory import create_provider
from payroll.application.provider import ServiceProvider
from payroll.web.routes import router
from payroll.web.schemas.login import LoginInput
from payroll.web.session_store import SessionStore


def create_web_application(provider: ServiceProvider | None = None) -> FastAPI:
    """Подключает сервисы и UI; не создаёт таблицы и не запускает миграции."""

    app = FastAPI(title="Salary Calculator", version="0.4.0")
    app.state.provider = provider or create_provider()
    app.state.sessions = SessionStore()
    frontend = Path(__file__).resolve().parents[3] / "frontend"

    @app.exception_handler(ValueError)
    async def invalid_value(request: Request, error: ValueError) -> JSONResponse:
        """Показывает нарушение бизнес-правила без завершения сервера."""

        return JSONResponse({"message": str(error), "fields": {}}, status_code=400)

    @app.exception_handler(LookupError)
    async def missing_value(request: Request, error: LookupError) -> JSONResponse:
        """Сообщает об отсутствующей карточке или периоде."""

        return JSONResponse({"message": str(error), "fields": {}}, status_code=404)

    @app.exception_handler(PermissionError)
    async def forbidden(request: Request, error: PermissionError) -> JSONResponse:
        """Предлагает повторный вход без раскрытия внутреннего состояния."""

        return JSONResponse({"message": str(error), "fields": {}}, status_code=401)

    @app.exception_handler(StorageError)
    async def unavailable(request: Request, error: StorageError) -> JSONResponse:
        """Возвращает безопасную ошибку после отката SQL-провайдером."""

        return JSONResponse(
            {
                "message": "Хранилище недоступно. Повторите действие позже.",
                "fields": {},
            },
            status_code=503,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        """Сохраняет единый формат ошибок формы."""

        detail = error.detail
        body = (
            detail
            if isinstance(detail, dict)
            else {"message": str(detail), "fields": {}}
        )
        return JSONResponse(body, status_code=error.status_code, headers=error.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        """Связывает ошибки типов JSON с полями; возвращает требуемый код 400."""

        fields = {
            str(item["loc"][-1]): "Проверьте формат значения" for item in error.errors()
        }
        return JSONResponse({"message": "Проверьте поля формы", "fields": fields}, 400)

    @app.post("/api/login")
    def login(data: LoginInput, response: Response) -> dict[str, str]:
        """Выдаёт отдельный cookie-сеанс для учебного локального интерфейса."""

        token = app.state.sessions.login(data.username, data.password)
        response.set_cookie(
            "salary_session", token, httponly=True, samesite="strict", max_age=3600
        )
        return {"username": data.username}

    @app.post("/api/logout")
    def logout(request: Request, response: Response) -> dict[str, bool]:
        """Завершает текущий веб-сеанс."""

        app.state.sessions.logout(request.cookies.get("salary_session", ""))
        response.delete_cookie("salary_session")
        return {"ok": True}

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Выдаёт главную страницу с того же адреса, что и API."""

        return FileResponse(frontend / "index.html")

    app.include_router(router)
    app.mount("/assets", StaticFiles(directory=frontend), name="assets")
    return app
