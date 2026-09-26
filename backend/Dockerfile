FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.lock.txt .



RUN uv pip install --system --no-cache -r requirements.lock.txt


COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

EXPOSE 8000

# Aplica las migraciones pendientes antes de levantar la API. Requiere DATABASE_URL.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]