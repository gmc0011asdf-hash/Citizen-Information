@echo off
chcp 65001 >nul 2>&1
title Civil Information System
color 0B

echo.
echo  ============================================================
echo       Civil Information System - Starting...
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found. Run install.bat first.
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Node.js not found. Run install.bat first.
    pause
    exit /b 1
)

:: Check node_modules
if not exist "%~dp0frontend\node_modules" (
    echo  [ERROR] Frontend not installed. Run install.bat first.
    pause
    exit /b 1
)

:: Start Backend
echo  [1/2] Starting Backend API (port 8000)...
start "Civil Info - API" cmd /c "cd /d %~dp0backend && python -m uvicorn api:app --host 127.0.0.1 --port 8000"

echo        Waiting for API to start...
timeout /t 4 /nobreak >nul

:: Start Frontend (production if built, dev otherwise)
if exist "%~dp0frontend\.next" (
    echo  [2/2] Starting Frontend - Production (port 3000)...
    start "Civil Info - Frontend" cmd /c "cd /d %~dp0frontend && npm start"
) else (
    echo  [2/2] Starting Frontend - Development (port 3000)...
    start "Civil Info - Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"
)

echo        Waiting for Frontend to start...
timeout /t 6 /nobreak >nul

:: Open browser
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
