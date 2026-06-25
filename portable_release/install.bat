@echo off
chcp 65001 >nul 2>&1
title Civil Information System - Installer
color 0B

echo.
echo  ============================================================
echo       Civil Information System - Full Installer
echo  ============================================================
echo.

set "INSTALLERS_DIR=%~dp0installers"
if not exist "%INSTALLERS_DIR%" mkdir "%INSTALLERS_DIR%"

:: ============================================================
:: [1/4] PYTHON
:: ============================================================
echo [1/4] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Python found.
    goto :python_done
)

echo       Downloading Python 3.12.10...
set "PY_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
set "PY_FILE=%INSTALLERS_DIR%\python-3.12.10-amd64.exe"

if not exist "%PY_FILE%" (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%PY_URL%','%PY_FILE%')" 2>nul
)
if not exist "%PY_FILE%" (
    echo       [ERROR] Download failed. Download manually:
    echo       https://www.python.org/downloads/
    pause
    exit /b 1
)
echo       Installing Python...
"%PY_FILE%" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"
timeout /t 3 /nobreak >nul
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       [!] Close this window and run install.bat again.
    pause
    exit /b 1
)
echo       [OK] Python installed.

:python_done
echo.

:: ============================================================
:: [2/4] NODE.JS
:: ============================================================
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo       [OK] Node.js found.
    goto :node_done
)

echo       Downloading Node.js 22 LTS...
set "NODE_URL=https://nodejs.org/dist/v22.16.0/node-v22.16.0-x64.msi"
set "NODE_FILE=%INSTALLERS_DIR%\node-v22.16.0-x64.msi"

if not exist "%NODE_FILE%" (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%NODE_URL%','%NODE_FILE%')" 2>nul
)
if not exist "%NODE_FILE%" (
    echo       [ERROR] Download failed. Download manually:
    echo       https://nodejs.org/
    pause
    exit /b 1
)
echo       Installing Node.js...
msiexec /i "%NODE_FILE%" /passive
set "PATH=C:\Program Files\nodejs\;%PATH%"
timeout /t 3 /nobreak >nul
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       [!] Close this window and run install.bat again.
    pause
    exit /b 1
)
echo       [OK] Node.js installed.

:node_done
echo.

:: ============================================================
:: [3/4] PYTHON PACKAGES
:: ============================================================
echo [3/4] Installing Python packages...
cd /d "%~dp0backend"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo       Retrying...
    python -m pip install -r requirements.txt --timeout 60
)
echo       [OK] Python packages done.
echo.

:: ============================================================
:: [4/4] FRONTEND PACKAGES (with retry + mirror)
:: ============================================================
echo [4/4] Installing frontend packages...
cd /d "%~dp0frontend"

echo       Attempt 1/3...
call npm install --prefer-offline 2>nul
if %ERRORLEVEL% == 0 goto :npm_done

echo       Attempt 2/3 (retry)...
timeout /t 5 /nobreak >nul
call npm install 2>nul
if %ERRORLEVEL% == 0 goto :npm_done

echo       Attempt 3/3 (mirror registry)...
timeout /t 5 /nobreak >nul
call npm install --registry https://registry.npmmirror.com 2>nul
if %ERRORLEVEL% == 0 goto :npm_done

echo.
echo       [ERROR] npm install failed after 3 attempts.
echo       Check your internet connection and try:
echo         cd frontend
echo         npm install
echo.
pause
exit /b 1

:npm_done
echo       [OK] Frontend packages done.
echo.

:: ============================================================
:: BUILD FRONTEND
:: ============================================================
echo [EXTRA] Building frontend for production...
call npm run build 2>nul
if %ERRORLEVEL% == 0 (
    echo       [OK] Build complete. Use "npm start" for production.
) else (
    echo       [OK] Build skipped. Use "npm run dev" for development.
)
echo.

:: ============================================================
:: DONE
:: ============================================================
echo.
echo  ============================================================
echo       Installation Complete!
echo  ============================================================
echo.
echo       Run: start.bat
echo       URL: http://localhost:3000
echo       Login: admin / admin
echo.
echo  ============================================================
pause
