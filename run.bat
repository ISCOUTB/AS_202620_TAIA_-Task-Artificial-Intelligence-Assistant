@echo off
rem Base de datos local de desarrollo (usuario y contrasena taia, igual que en el CI).
if not defined DATABASE_URL set DATABASE_URL=postgresql+psycopg://taia:taia@localhost:5432/taia
rem Solo para desarrollo local; en despliegue viene del secreto TAIA_JWT_SECRET de GitHub.
if not defined TAIA_JWT_SECRET set TAIA_JWT_SECRET=dev-local-jwt-secret
python -m alembic -c backend/alembic.ini upgrade head || exit /b 1
python -m uvicorn app.main:app --app-dir backend --reload
