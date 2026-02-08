@echo off
echo Starting VibeCober Backend (API)...
cd /d "%~dp0"

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
