@echo off
chcp 65001 > nul
title Build Portable Release

set "SRC=%~dp0"
set "OUT=%SRC%portable_release"

echo ============================================
echo   Building Portable Release
echo ============================================

if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
mkdir "%OUT%\backend"
mkdir "%OUT%\backend\data"
mkdir "%OUT%\frontend"

echo [1/5] Copying backend files...
copy /Y "%SRC%api.py" "%OUT%\backend\" > nul
copy /Y "%SRC%db_ali.py" "%OUT%\backend\" > nul
copy /Y "%SRC%cleaner.py" "%OUT%\backend\" > nul
copy /Y "%SRC%requirements_api.txt" "%OUT%\backend\requirements.txt" > nul

echo [2/5] Copying database...
if exist "%SRC%data\ali_gharbi.db" (
    copy /Y "%SRC%data\ali_gharbi.db" "%OUT%\backend\data\" > nul
    echo    Database copied.
) else (
    echo    WARNING: No database found. A new one will be created.
)
if exist "%SRC%data\backups" (
    mkdir "%OUT%\backend\data\backups" 2>nul
    xcopy /Y /Q "%SRC%data\backups\*.db" "%OUT%\backend\data\backups\" > nul 2>&1
)

echo [3/5] Copying frontend...
xcopy /E /I /Q /Y "%SRC%civil-info-next" "%OUT%\frontend" /exclude:%SRC%portable_exclude.txt > nul 2>&1

echo [4/5] Creating launch scripts...

rem --- install script ---
> "%OUT%\install.bat" (
echo @echo off
echo chcp 65001 ^> nul
echo title Install Civil Info System
echo echo.
echo echo ============================================
echo echo   Installing Civil Information System
echo echo ============================================
echo echo.
echo python --version ^>nul 2^>^&1
echo IF ERRORLEVEL 1 ^(
echo     echo [ERROR] Python not installed. Install Python 3.11+
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Python found.
echo echo.
echo echo Installing Python packages...
echo cd /d "%%~dp0backend"
echo python -m pip install --upgrade pip ^>nul 2^>^&1
echo python -m pip install -r requirements.txt
echo echo.
echo node --version ^>nul 2^>^&1
echo IF ERRORLEVEL 1 ^(
echo     echo [ERROR] Node.js not installed. Install Node.js LTS
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Node.js found.
echo echo.
echo echo Installing frontend packages...
echo cd /d "%%~dp0frontend"
echo npm install
echo echo.
echo echo ============================================
echo echo   Installation complete!
echo echo   Run start.bat to launch the system.
echo echo ============================================
echo pause
)

rem --- start script ---
> "%OUT%\start.bat" (
echo @echo off
echo chcp 65001 ^> nul
echo title Civil Information System
echo echo Starting Backend API...
echo start "API Server" cmd /k "cd /d %%~dp0backend ^&^& python -m uvicorn api:app --host 127.0.0.1 --port 8000"
echo timeout /t 3 /nobreak ^>nul
echo echo Starting Frontend...
echo start "Frontend" cmd /k "cd /d %%~dp0frontend ^&^& npm run dev"
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:3000
echo echo.
echo echo ============================================
echo echo   System is running:
echo echo   Frontend: http://localhost:3000
echo echo   Backend:  http://localhost:8000/docs
echo echo   Login: admin / admin
echo echo ============================================
echo pause
)

echo [5/5] Creating README...

> "%OUT%\README.txt" (
echo ============================================
echo   Civil Information System
echo   نظام المعلومات المدنية للمواطنين
echo ============================================
echo.
echo REQUIREMENTS:
echo   - Python 3.11 or later
echo   - Node.js 18 or later
echo.
echo INSTALLATION:
echo   1. Run install.bat (once only^)
echo.
echo USAGE:
echo   1. Run start.bat
echo   2. Open http://localhost:3000
echo   3. Login: admin / admin
echo.
echo DATABASE:
echo   backend\data\ali_gharbi.db
echo   Do NOT delete this file.
echo.
echo BACKUP:
echo   Copy backend\data\ali_gharbi.db
echo.
echo DEVELOPER:
echo   Ahmed Al-Thahabi
echo   07711228946
echo   07822667735
)

echo.
echo ============================================
echo   Portable release created at:
echo   %OUT%
echo ============================================
pause
