@echo off
title aififteen Hunter Watchdog
cd /d "%~dp0"
if not exist "backend\.env" (
  copy backend\.env.example backend\.env >nul
)
cd /d "%~dp0backend"
set PYTHONPATH=%~dp0backend;%~dp0backend\vendor
if not exist "%~dp0logs" mkdir "%~dp0logs"

echo ============================================================
echo  aififteen Hunter Watchdog running
echo  Backend auto-restarts 3s after crash. Close window = stop.
echo  Log: logs\watchdog.log
echo ============================================================

:loop
echo [%date% %time%] [watchdog] starting backend (uvicorn 18800)...
python -m uvicorn app.main:app --host 0.0.0.0 --port 18800 >> "%~dp0logs\watchdog.log" 2>&1
echo [%date% %time%] [watchdog] backend exited (code %errorlevel%), restart in 3s...
timeout /t 3 /nobreak >nul
goto loop
