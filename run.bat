@echo off
rem Base de datos local de desarrollo (usuario y contrasena taia, igual que en el CI).
if not defined DATABASE_URL set DATABASE_URL=postgresql+psycopg://taia:taia@localhost:5432/taia
python -m alembic -c backend/alembic.ini upgrade head || exit /b 1
python -m uvicorn app.main:app --app-dir backend --reload
