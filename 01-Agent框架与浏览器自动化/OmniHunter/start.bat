@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ============================================================
REM  aififteen Hunter one-click start
REM  usage:  start.bat        (dev mode: backend 18800 + frontend 5173)
REM          start.bat prod   (prod mode: build UI, serve at 18800)
REM ============================================================

set MODE=%1
if "%MODE%"=="" set MODE=dev

echo ================================================
echo   aififteen Hunter - one-click start [%MODE%]
echo ================================================

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ first.
  pause & exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js not found. Install Node 18+ first.
  pause & exit /b 1
)

REM ---- [1/4] backend deps -> vendor (sandbox friendly) ----
if not exist "backend\vendor\httpx" (
  echo [1/4] Installing backend deps into backend\vendor ...
  pushd backend
  python -m pip install --target=vendor -r requirements.txt
  python -m pip install --target=vendor bandit dlint mitmproxy bcrypt jinja2
  popd
) else (
  echo [1/4] Backend deps OK
)

REM ---- [2/4] .env ----
if not exist "backend\.env" (
  echo [2/4] Creating backend\.env from template ...
  copy backend\.env.example backend\.env >nul
  echo        Please edit backend\.env and fill LLM_API_KEY.
) else (
  echo [2/4] backend\.env OK
)

REM ---- [3/4] frontend deps ----
if not exist "frontend\node_modules" (
  echo [3/4] Installing frontend deps ...
  pushd frontend
  call npm install
  popd
) else (
  echo [3/4] Frontend deps OK
)

REM ---- [4/4] start ----
if /i "%MODE%"=="prod" (
  echo [4/4] Building frontend ...
  pushd frontend
  call npm run build
  popd
  echo Starting backend at http://localhost:18800 ^(serves built UI^) ...
  start "aififteen-backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 18800"
  timeout /t 6 /nobreak >nul
  start http://localhost:18800
) else (
  echo [4/4] Starting backend + frontend dev server ...
  start "aififteen-backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18800"
  start "aififteen-frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
  timeout /t 8 /nobreak >nul
  start http://localhost:5173
)

echo.
echo Done.  Backend: http://localhost:18800/docs   UI: http://localhost:5173 (dev) / 18800 (prod)
echo Stop:   double-click stop.bat
pause
