@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ============================================================
REM  aififteen Hunter offline deploy (run on target server)
REM  1. docker load image
REM  2. prepare .env
REM  3. docker compose up -d  ->  http://localhost:18800
REM ============================================================

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker not found on this machine.
  pause & exit /b 1
)

echo [1/3] Loading image ...
docker load -i aififteen-hunter-image.tar
if errorlevel 1 ( echo [ERROR] docker load failed & pause & exit /b 1 )

echo [2/3] Preparing .env ...
if not exist backend\.env (
  mkdir backend 2>nul
  copy env.example backend\.env >nul
  echo        Created backend\.env - EDIT IT and fill LLM_API_KEY, then rerun this script.
  notepad backend\.env
)

echo [3/3] Starting container ...
docker compose up -d
if errorlevel 1 ( echo [ERROR] compose up failed & pause & exit /b 1 )

timeout /t 5 /nobreak >nul
start http://localhost:18800
echo.
echo Done. aififteen Hunter: http://localhost:18800
echo Logs: docker compose logs -f    Stop: docker compose down
pause
