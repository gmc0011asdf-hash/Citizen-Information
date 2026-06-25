@echo off
chcp 65001 >nul 2>&1
title Civil Information System

echo Starting system...

start /min "" cmd /c "cd /d %~dp0backend && python -m uvicorn api:app --host 127.0.0.1 --port 8000 >nul 2>&1"

timeout /t 4 /nobreak >nul

start /min "" cmd /c "cd /d %~dp0frontend && npm run dev >nul 2>&1"

timeout /t 6 /nobreak >nul

start http://localhost:3000

exit
