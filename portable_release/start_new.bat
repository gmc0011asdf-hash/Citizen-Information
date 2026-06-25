@echo off
chcp 65001 >nul 2>&1
title Civil Information System
color 0B

echo.
echo  ============================================================
echo       Civil Information System - Starting...
echo  ============================================================
echo.

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found. Run install.bat first.
    pause
    exit /b 1
)

node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Node.js not found. Run install.bat first.
    pause
    exit /b 1
)

echo  [1/2] Starting Backend API (port 8000)...
start "Civil Info - API" cmd /k "cd /d %~dp0backend && python -m uvicorn api:app --host 127.0.0.1 --port 8000"

echo        Waiting for API...
timeout /t 4 /nobreak >nul

echo  [2/2] Starting Frontend (port 3000)...
start "Civil Info - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo        Waiting for Frontend...
timeout /t 6 /nobreak >nul

start http://localhost:3000

echo.
echo  ============================================================
echo       System is running!
echo  ============================================================
echo.
echo       Frontend: http://localhost:3000
echo       Backend:  http://localhost:8000/docs
echo       Login:    admin / admin
echo.
echo       To stop: close the two CMD windows
echo  ============================================================
echo.
pause
