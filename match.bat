@echo off
chcp 65001 > nul
title Excel Matcher - نظام المطابقة

echo ============================================================
echo   Excel Matcher - مطابقة ملف Excel مع قاعدة البيانات
echo ============================================================
echo.

REM التحقق من وجود Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [!] Python غير مثبت. يرجى تثبيت Python 3.8 او احدث.
    pause
    exit /b 1
)

REM التحقق من وجود قاعدة البيانات
if not exist "data\excel_filter.db" (
    echo [!] قاعدة البيانات غير موجودة.
    echo     يرجى تشغيل run.bat اولا لاستيراد ملف Excel.
    pause
    exit /b 1
)

REM ضبط الترميز UTF-8
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM تشغيل برنامج المطابقة
echo [*] جاري تشغيل نظام المطابقة...
echo     ملاحظة: قد تستغرق المطابقة بعض الوقت حسب حجم الملفين
echo.
python match_excel.py

if errorlevel 1 (
    echo.
    echo [!] توقف البرنامج بسبب خطا.
)

echo.
echo ============================================================
echo   النتائج محفوظة في مجلد: data\exports
echo ============================================================
pause
