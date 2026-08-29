@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

REM ============================================================
REM  Pack aififteen Hunter Docker offline bundle
REM  run this on a machine WITH docker + network:
REM    deploy\pack-offline.bat
REM  output: aififteen-hunter-offline.zip
REM  on the target server: unzip -> run load-and-up.bat
REM ============================================================

echo [1/4] Building image (docker compose build) ...
docker compose build
if errorlevel 1 ( echo [ERROR] build failed & pause & exit /b 1 )

echo [2/4] Saving image aififteen-hunter:latest ...
if exist aififteen-hunter-image.tar del aififteen-hunter-image.tar
docker save -o aififteen-hunter-image.tar aififteen-hunter:latest
if errorlevel 1 ( echo [ERROR] docker save failed & pause & exit /b 1 )

echo [3/4] Collecting bundle files ...
if exist aififteen-hunter-offline rmdir /s /q aififteen-hunter-offline
mkdir aififteen-hunter-offline
copy /y aififteen-hunter-image.tar aififteen-hunter-offline\ >nul
copy /y docker-compose.yml aififteen-hunter-offline\ >nul
copy /y backend\.env.example aififteen-hunter-offline\env.example >nul
copy /y deploy\load-and-up.bat aififteen-hunter-offline\ >nul
del aififteen-hunter-image.tar

echo [4/4] Zipping ...
powershell -NoProfile -Command "Compress-Archive -Path 'aififteen-hunter-offline\*' -DestinationPath 'aififteen-hunter-offline.zip' -Force"
rmdir /s /q aififteen-hunter-offline

echo.
echo Done: aififteen-hunter-offline.zip
echo Target server (docker installed, no network needed):
echo   1. unzip aififteen-hunter-offline.zip
echo   2. edit .env ^(fill LLM_API_KEY^)
echo   3. run load-and-up.bat
pause
