FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY backend/requirements.lock.txt ./requirements.lock.txt



RUN uv pip install --system --no-cache -r requirements.lock.txt


COPY backend/app ./app
COPY backend/alembic.ini .
COPY backend/alembic ./alembic


EXPOSE 8000

# Aplica las migraciones pendientes antes de levantar la API. Requiere DATABASE_URL.
# Sin access log de uvicorn: la API escribe su propio log JSON por petición.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]