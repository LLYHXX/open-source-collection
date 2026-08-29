#!/usr/bin/env bash
# aififteen Hunter · 图形化启动器（Linux / macOS 桌面壳）
cd "$(dirname "$0")"
MODE="${1:-dev}"
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] 未找到 python3"; exit 1; }
python3 gui_launcher.py "$MODE"
