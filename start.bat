@echo off
echo VibeCober - Single Server (Frontend + Backend on port 8000)
cd /d "%~dp0"

echo Building frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo Frontend build failed.
    exit /b 1
)
cd ..

echo.
echo Starting server at http://127.0.0.1:8000
echo.
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
