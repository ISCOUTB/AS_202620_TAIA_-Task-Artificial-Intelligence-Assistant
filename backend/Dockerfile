FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 /uv /uvx /bin/

WORKDIR /app

RUN useradd --create-home appuser

COPY backend/requirements.lock.txt ./requirements.lock.txt



RUN chown -R appuser:appuser /app \
;  uv pip install --system --no-cache --require-hashes --only-binary :all: -r requirements.lock.txt


COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser backend/alembic.ini .
COPY --chown=appuser:appuser backend/alembic ./alembic

USER appuser

EXPOSE 8000

# Aplica las migraciones pendientes antes de levantar la API. Requiere DATABASE_URL.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
