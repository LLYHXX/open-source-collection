@echo off
chcp 65001 >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v aififteenHunter /t REG_SZ /d "\"%~dp0autostart.bat\"" /f >nul
echo [OK] 已注册开机自启动（当前用户）
echo      每次登录 Windows 后自动后台启动生产模式后端 http://localhost:18800
echo      移除请双击 uninstall_autostart.bat
pause
