@echo off
REM ============================================================
REM  aififteen Hunter 开机自启动入口
REM  由 install_autostart.bat 注册到 HKCU\...\Run，登录后静默拉起
REM  生产模式后端（18800 托管前端构建产物）；关掉最小化窗口=停止服务
REM ============================================================
cd /d "%~dp0"
if not exist "backend\.env" (
  copy backend\.env.example backend\.env >nul
)
cd /d "%~dp0backend"
start "aififteen-hunter" /min cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 18800"
