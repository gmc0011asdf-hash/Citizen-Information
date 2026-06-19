@echo off
chcp 65001 > nul
title Excel Filter - نظام الفلترة والاستيراد

echo ============================================================
echo   Excel to SQLite - نظام استيراد Excel إلى قاعدة البيانات
echo ============================================================
echo.

REM التحقق من وجود Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [!] Python غير مثبت. يرجى تثبيت Python 3.8 أو أحدث.
    pause
    exit /b 1
)

REM التحقق من وجود المكتبات
python -c "import pandas, openpyxl, rapidfuzz" > nul 2>&1
if errorlevel 1 (
    echo [!] بعض المكتبات غير مثبتة. جارٍ التثبيت...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [!] فشل تثبيت المكتبات. يرجى تشغيل: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [+] تم تثبيت المكتبات بنجاح.
    echo.
)

REM ضبط الترميز UTF-8 لدعم العربية
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM تشغيل البرنامج
echo [*] جارٍ تشغيل البرنامج...
python main.py

if errorlevel 1 (
    echo.
    echo [!] توقف البرنامج بسبب خطأ.
)

echo.
echo ============================================================
pause
