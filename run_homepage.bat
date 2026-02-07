@echo off
echo Starting VibeCober Homepage...

cd frontend

if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

echo Opening browser...
start "" "http://localhost:3000"

echo Starting Vite dev server...
npm run dev
