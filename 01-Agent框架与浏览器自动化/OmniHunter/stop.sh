#!/usr/bin/env bash
# aififteen Hunter 一键停止（先按 start.sh 记录的 pid 停，再按端口兜底清理）
cd "$(dirname "$0")"

stopped=0
for f in .run/backend.pid .run/frontend.pid; do
  if [ -f "$f" ]; then
    pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && { echo "已停止 $(basename "$f" .pid) (pid $pid)"; stopped=1; }
    fi
    rm -f "$f"
  fi
done

# 兜底：按端口清理残留（18800 后端 / 5173 前端）
for port in 18800 5173; do
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null && { echo "已清理端口 $port"; stopped=1; }
  elif command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti tcp:"$port" 2>/dev/null)
    if [ -n "$pids" ]; then
      kill $pids 2>/dev/null && { echo "已清理端口 $port"; stopped=1; }
    fi
  fi
done

[ "$stopped" = "0" ] && echo "没有正在运行的服务"
exit 0
