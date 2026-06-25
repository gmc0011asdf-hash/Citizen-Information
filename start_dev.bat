@echo off
title Civil Info System
echo Starting Backend...
start "API" cmd /k "cd /d E:\PROJACT-AHMEDxcel-filter && python -m uvicorn api:app --host 127.0.0.1 --port 8000"
timeout /t 4 /nobreak >nul
echo Starting Frontend...
start "Frontend" cmd /k "cd /d E:\PROJACT-AHMEDxcel-filter\civil-info-next && npm run dev"
timeout /t 6 /nobreak >nul
start http://localhost:3000
echo.
echo System running at http://localhost:3000
echo Login: admin / admin
pause
