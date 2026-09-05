@echo off
echo Stopping aififteen Hunter (watchdog + ports 18800 / 5173) ...

REM 1) Kill watchdog first (otherwise it restarts backend in 3s)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'cmd.exe' -and $_.CommandLine -like '*watchdog.bat*') -or ($_.Name -eq 'wscript.exe' -and $_.CommandLine -like '*watchdog_silent.vbs*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('  stopped watchdog PID ' + $_.ProcessId) }"

REM 2) Kill backend/frontend listening on ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":18800 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul && echo   stopped PID %%a (18800)
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>nul && echo   stopped PID %%a (5173)
)

echo Done.
pause
