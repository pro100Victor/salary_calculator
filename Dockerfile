FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.docker.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
COPY frontend ./frontend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "salary_calculator.web.app:create_web_application", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS tests
COPY tests ./tests
COPY pyproject.toml ./
RUN pip install --no-cache-dir pytest==9.1.1 httpx==0.28.1

FROM runtime AS production
