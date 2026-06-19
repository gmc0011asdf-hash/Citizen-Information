@echo off
chcp 65001 > nul
title Civil Information System
echo.
echo ============================================
echo   Civil Information System - Starting...
echo ============================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo [1/2] Starting API server on port 8000...
start /B python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

echo [2/2] Starting Next.js on port 3000...
cd civil-info-next
npm run dev
