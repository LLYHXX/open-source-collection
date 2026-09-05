@echo off
chcp 65001 >nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v aififteenHunter /f >nul 2>nul
echo [OK] 已移除开机自启动
pause
