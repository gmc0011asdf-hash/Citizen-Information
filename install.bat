@echo off
chcp 65001 > nul
title تثبيت نظام المعلومات المدنية للمواطنين

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     🏛️  تثبيت نظام المعلومات المدنية للمواطنين         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ─── التحقق من Python ───
python --version > nul 2>&1
if errorlevel 1 (
    echo [!] Python غير مثبت على هذا الجهاز.
    echo [!] حمّل Python من: https://www.python.org/downloads/
    echo [!] تأكد من تفعيل خيار "Add to PATH" أثناء التثبيت.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [✓] Python %PYVER% موجود.
echo.

REM ─── اختيار مكان التثبيت ───
echo ────────────────────────────────────────────────
echo   اختر مكان تثبيت النظام:
echo ────────────────────────────────────────────────
echo.
echo   [1] سطح المكتب  (Desktop)
echo   [2] القرص C      (C:\المعلومات_المدنية)
echo   [3] القرص D      (D:\المعلومات_المدنية)
echo   [4] مكان مخصص
echo.
set /p CHOICE="  اختيارك (1-4): "

if "%CHOICE%"=="1" set "INSTALL_DIR=%USERPROFILE%\Desktop\المعلومات_المدنية"
if "%CHOICE%"=="2" set "INSTALL_DIR=C:\المعلومات_المدنية"
if "%CHOICE%"=="3" set "INSTALL_DIR=D:\المعلومات_المدنية"
if "%CHOICE%"=="4" (
    set /p "INSTALL_DIR=  أدخل المسار الكامل: "
)

if "%INSTALL_DIR%"=="" (
    echo [!] لم يتم اختيار مكان صحيح.
    pause
    exit /b 1
)

echo.
echo [*] مكان التثبيت: %INSTALL_DIR%
echo.

REM ─── إنشاء المجلد ───
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo [✓] تم إنشاء المجلد.
) else (
    echo [!] المجلد موجود مسبقاً. سيتم تحديث الملفات.
)

REM ─── نسخ ملفات المشروع ───
echo [*] جارٍ نسخ ملفات النظام...
set "SRC=%~dp0"

copy /Y "%SRC%app.py"             "%INSTALL_DIR%\" > nul
copy /Y "%SRC%db_ali.py"          "%INSTALL_DIR%\" > nul
copy /Y "%SRC%cleaner.py"         "%INSTALL_DIR%\" > nul
copy /Y "%SRC%crud.py"            "%INSTALL_DIR%\" > nul
copy /Y "%SRC%db.py"              "%INSTALL_DIR%\" > nul
copy /Y "%SRC%importer.py"        "%INSTALL_DIR%\" > nul
copy /Y "%SRC%main.py"            "%INSTALL_DIR%\" > nul
copy /Y "%SRC%match_excel.py"     "%INSTALL_DIR%\" > nul
copy /Y "%SRC%search.py"          "%INSTALL_DIR%\" > nul
copy /Y "%SRC%export_results.py"  "%INSTALL_DIR%\" > nul
copy /Y "%SRC%analytics.py"       "%INSTALL_DIR%\" > nul
copy /Y "%SRC%ui_helpers.py"      "%INSTALL_DIR%\" > nul
copy /Y "%SRC%requirements.txt"   "%INSTALL_DIR%\" > nul
copy /Y "%SRC%run_ui.bat"         "%INSTALL_DIR%\" > nul
copy /Y "%SRC%run.bat"            "%INSTALL_DIR%\" > nul
copy /Y "%SRC%match.bat"          "%INSTALL_DIR%\" > nul
copy /Y "%SRC%README.md"          "%INSTALL_DIR%\" > nul

echo [✓] تم نسخ ملفات النظام.

REM ─── نسخ قاعدة البيانات ───
if not exist "%INSTALL_DIR%\data" mkdir "%INSTALL_DIR%\data"

if exist "%SRC%data\ali_gharbi.db" (
    if exist "%INSTALL_DIR%\data\ali_gharbi.db" (
        echo.
        echo [!] قاعدة بيانات موجودة في مكان التثبيت.
        set /p DBCHOICE="    هل تريد استبدالها بالبيانات الحالية؟ (نعم/لا): "
        if /i "%DBCHOICE%"=="نعم" (
            copy /Y "%SRC%data\ali_gharbi.db" "%INSTALL_DIR%\data\" > nul
            echo [✓] تم نسخ قاعدة البيانات.
        ) else (
            echo [*] تم الاحتفاظ بقاعدة البيانات الموجودة.
        )
    ) else (
        copy /Y "%SRC%data\ali_gharbi.db" "%INSTALL_DIR%\data\" > nul
        echo [✓] تم نسخ قاعدة البيانات.
    )
) else (
    echo [*] لا توجد قاعدة بيانات للنسخ. سيتم إنشاؤها تلقائياً عند التشغيل.
)

REM ─── نسخ النسخ الاحتياطية ───
if exist "%SRC%data\backups" (
    if not exist "%INSTALL_DIR%\data\backups" mkdir "%INSTALL_DIR%\data\backups"
    xcopy /Y /Q "%SRC%data\backups\*.db" "%INSTALL_DIR%\data\backups\" > nul 2>&1
    echo [✓] تم نسخ النسخ الاحتياطية.
)

REM ─── تثبيت المكتبات ───
echo.
echo [*] جارٍ تثبيت المكتبات المطلوبة...
python -m pip install --upgrade pip > nul 2>&1
python -m pip install -r "%INSTALL_DIR%\requirements.txt" > nul 2>&1
if errorlevel 1 (
    echo [!] فشل تثبيت بعض المكتبات. حاول يدوياً:
    echo     pip install -r "%INSTALL_DIR%\requirements.txt"
) else (
    echo [✓] تم تثبيت جميع المكتبات.
)

REM ─── إنشاء اختصار على سطح المكتب ───
echo.
set /p SHORTCUT="  هل تريد إنشاء اختصار على سطح المكتب؟ (نعم/لا): "
if /i "%SHORTCUT%"=="نعم" (
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo cd /d "%INSTALL_DIR%"
        echo set PYTHONIOENCODING=utf-8
        echo set PYTHONUTF8=1
        echo python -m streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false --theme.base light
    ) > "%USERPROFILE%\Desktop\المعلومات المدنية.bat"
    echo [✓] تم إنشاء الاختصار على سطح المكتب.
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║              ✅ تم التثبيت بنجاح!                       ║
echo ╠══════════════════════════════════════════════════════════╣
echo ║  مكان التثبيت: %INSTALL_DIR%
echo ║  للتشغيل: افتح run_ui.bat من مجلد التثبيت              ║
echo ║  أو اضغط اختصار سطح المكتب                             ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
pause
