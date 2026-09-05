@echo off
REM ============================================================
REM  aififteen Hunter autostart (watchdog mode)
REM  Registered by install_autostart.bat to HKCU\...\Run
REM  Watchdog: backend auto-restarts 3s after crash
REM  Stop: run stop.bat, or kill cmd watchdog + python in Task Manager
REM ============================================================
cd /d "%~dp0"
wscript.exe "%~dp0watchdog_silent.vbs"
