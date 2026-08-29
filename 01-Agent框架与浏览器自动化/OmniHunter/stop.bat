@echo off
chcp 65001 >nul
echo Stopping aififteen Hunter (ports 18800 / 5173) ...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":18800 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul && echo   stopped PID %%a (18800)
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul && echo   stopped PID %%a (5173)
)

echo Done.
pause
