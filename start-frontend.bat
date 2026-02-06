@echo off
echo Starting VibeCober Frontend (frontend-1)...
cd frontend-1

if not exist node_modules (
	echo Installing frontend dependencies...
	npm install
)

npm run dev
