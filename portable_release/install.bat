@echo off
chcp 65001 >nul 2>&1
title Civil Information System - Installer
color 0B

echo.
echo  ============================================================
echo       Civil Information System - Full Installer
echo       ------------------------------------------
echo       This will install Python, Node.js, and all
echo       dependencies needed to run the system.
echo  ============================================================
echo.

set "INSTALLERS_DIR=%~dp0installers"
if not exist "%INSTALLERS_DIR%" mkdir "%INSTALLERS_DIR%"

:: ============================================================
:: CHECK AND INSTALL PYTHON
:: ============================================================
echo [1/4] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Python is already installed.
    python --version
    goto :python_done
)

echo       Python not found. Downloading Python 3.12.10...
echo.

set "PY_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
set "PY_INSTALLER=%INSTALLERS_DIR%\python-3.12.10-amd64.exe"

if exist "%PY_INSTALLER%" (
    echo       Installer already downloaded.
) else (
    echo       Downloading from: %PY_URL%
    echo       Please wait...
    powershell -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_INSTALLER%'" 2>nul
    if not exist "%PY_INSTALLER%" (
        echo.
        echo       [ERROR] Download failed!
        echo       Please download Python manually from:
        echo       https://www.python.org/downloads/
        echo       Make sure to check "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
)

echo       Installing Python (this may take a few minutes)...
echo       IMPORTANT: Python will be added to PATH automatically.
"%PY_INSTALLER%" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1

:: Refresh PATH
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"

timeout /t 3 /nobreak >nul

python --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Python installed successfully!
    python --version
) else (
    echo.
    echo       [WARNING] Python installed but PATH not updated yet.
    echo       Please CLOSE this window, REOPEN it, and run install.bat again.
    echo.
    pause
    exit /b 1
)

:python_done
echo.

:: ============================================================
:: CHECK AND INSTALL NODE.JS
:: ============================================================
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Node.js is already installed.
    node --version
    goto :node_done
)

echo       Node.js not found. Downloading Node.js 22 LTS...
echo.

set "NODE_URL=https://nodejs.org/dist/v22.16.0/node-v22.16.0-x64.msi"
set "NODE_INSTALLER=%INSTALLERS_DIR%\node-v22.16.0-x64.msi"

if exist "%NODE_INSTALLER%" (
    echo       Installer already downloaded.
) else (
    echo       Downloading from: %NODE_URL%
    echo       Please wait...
    powershell -Command "Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_INSTALLER%'" 2>nul
    if not exist "%NODE_INSTALLER%" (
        echo.
        echo       [ERROR] Download failed!
        echo       Please download Node.js manually from:
        echo       https://nodejs.org/
        echo.
        pause
        exit /b 1
    )
)

echo       Installing Node.js (this may take a few minutes)...
msiexec /i "%NODE_INSTALLER%" /passive

:: Refresh PATH
set "PATH=C:\Program Files\nodejs\;%PATH%"

timeout /t 3 /nobreak >nul

node --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Node.js installed successfully!
    node --version
) else (
    echo.
    echo       [WARNING] Node.js installed but PATH not updated yet.
    echo       Please CLOSE this window, REOPEN it, and run install.bat again.
    echo.
    pause
    exit /b 1
)

:node_done
echo.

:: ============================================================
:: INSTALL PYTHON PACKAGES
:: ============================================================
echo [3/4] Installing Python packages (FastAPI, uvicorn, pandas...)...
cd /d "%~dp0backend"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo       [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)
echo       [OK] Python packages installed.
echo.

:: ============================================================
:: INSTALL FRONTEND PACKAGES
:: ============================================================
echo [4/4] Installing frontend packages (Next.js, React...)...
cd /d "%~dp0frontend"
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo       [ERROR] Failed to install frontend packages.
    pause
    exit /b 1
)
echo       [OK] Frontend packages installed.
echo.

:: ============================================================
:: DONE
:: ============================================================
echo.
echo  ============================================================
echo       Installation Complete!
echo  ============================================================
echo.
echo       To start the system, run:  start.bat
echo.
echo       Login:    admin / admin
echo       URL:      http://localhost:3000
echo.
echo  ============================================================
pause
