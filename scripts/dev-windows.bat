@echo off
cd /d "%~dp0"
docker compose up -d
echo Waiting for Postgres...
timeout /t 8 /nobreak >nul
start "InsightBridge API" cmd /k "cd apps\api && .venv\Scripts\uvicorn insightbridge.main:app --reload --port 8000"
start "InsightBridge Web" cmd /k "cd apps\web && set NEXT_PUBLIC_API_URL=http://localhost:8000&& npm run dev"
echo Open http://localhost:3000
