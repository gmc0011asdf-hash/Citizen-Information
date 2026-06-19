@echo off
chcp 65001 > nul
title المعلومات المدنية للمواطنين

echo ============================================================
echo   المعلومات المدنية للمواطنين - واجهة إدارة البيانات
echo ============================================================
echo.

REM التحقق من وجود Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [!] Python غير مثبت.
    pause
    exit /b 1
)

REM التحقق من Streamlit
python -c "import streamlit" > nul 2>&1
if errorlevel 1 (
    echo [!] Streamlit غير مثبت. جارٍ التثبيت...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [!] فشل التثبيت.
        pause
        exit /b 1
    )
)

REM ضبط الترميز
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo [*] جارٍ تشغيل الواجهة...
echo [*] الرابط: http://localhost:8501
echo [*] اضغط Ctrl+C لإيقاف الواجهة
echo.

python -m streamlit run app.py ^
    --server.port 8501 ^
    --server.headless false ^
    --browser.gatherUsageStats false ^
    --theme.base light

echo.
echo [*] تم إيقاف الواجهة.
pause
