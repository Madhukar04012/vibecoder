@echo off
echo Starting VibeCober Backend (API)...
cd /d "%~dp0"

REM Activate virtual environment and start backend
call .venv\Scripts\activate.bat
python -m uvicorn backend.main:app --reload --reload-exclude generated_projects --host 0.0.0.0 --port 8000
