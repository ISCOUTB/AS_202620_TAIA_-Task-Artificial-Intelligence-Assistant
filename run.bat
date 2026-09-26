@echo off
python -m uvicorn app.main:app --app-dir backend --reload
