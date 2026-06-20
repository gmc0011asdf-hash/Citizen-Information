@echo off
title Civil Information System
echo Starting Backend API...
start "API Server" cmd /k "cd /d %~dp0backend && python -m uvicorn api:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
echo Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo.
echo ============================================
echo   System Running:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000/docs
echo   Login: admin / admin
echo ============================================
pause
