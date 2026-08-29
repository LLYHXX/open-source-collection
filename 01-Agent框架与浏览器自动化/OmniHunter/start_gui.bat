@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM aififteen Hunter · 图形化启动器（双击即起桌面控制窗口）
REM 用法：start_gui.bat      (开发模式，与 start.bat 对齐)
REM       start_gui.bat prod (生产模式，仅托管构建后的前端)

set MODE=%1
if "%MODE%"=="" set MODE=dev

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ first.
  pause & exit /b 1
)

REM 启动图形化桌面壳（Tkinter 窗口内含启动服务、停止、开界面等按钮）
echo Starting aififteen Hunter GUI launcher (%MODE%) ...
python gui_launcher.py %MODE%
