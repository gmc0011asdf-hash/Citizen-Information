@echo off
chcp 65001 > nul
title Citizen Information System
echo.
echo ============================================
echo   Citizen Information System
echo ============================================
echo.

python --version > /dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    pause
    exit /b 1
)

python -c "import streamlit" > /dev/null 2>&1
if errorlevel 1 (
    echo [*] Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Installation failed.
        pause
        exit /b 1
    )
)

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo [*] Starting server...
echo [*] URL: http://localhost:8501
echo [*] Press Ctrl+C to stop
echo.

python -m streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false --theme.base light

echo.
echo [*] Server stopped.
pause
