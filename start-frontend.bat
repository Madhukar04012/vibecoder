@echo off
echo Starting VibeCober Frontend (frontend)...
cd frontend

if not exist node_modules (
	echo Installing frontend dependencies...
	npm install
)

npm run dev
