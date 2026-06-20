@echo off
title Install Civil Info System
echo.
echo ============================================
echo   Installing Civil Information System
echo ============================================
echo.
python --version >/dev/null 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not installed.
    pause
    exit /b 1
)
echo [OK] Python found.
echo Installing Python packages...
cd /d "%~dp0backend"
python -m pip install --upgrade pip >/dev/null 2>&1
python -m pip install -r requirements.txt
echo.
node --version >/dev/null 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Node.js not installed.
    pause
    exit /b 1
)
echo [OK] Node.js found.
echo Installing frontend packages...
cd /d "%~dp0frontend"
npm install
echo.
echo ============================================
echo   Installation complete!
echo   Run start.bat to launch the system.
echo ============================================
pause
