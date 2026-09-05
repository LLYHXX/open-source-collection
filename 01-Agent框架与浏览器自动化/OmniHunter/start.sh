#!/usr/bin/env bash
# ============================================================
#  aififteen Hunter 一键启动（Linux / macOS）
#  用法:  ./start.sh        开发模式：后端 18800 + 前端 5173
#         ./start.sh prod   生产模式：构建前端由后端托管，访问 18800
# ============================================================
set -e
cd "$(dirname "$0")"
MODE="${1:-dev}"

echo "================================================"
echo "  aififteen Hunter - one-click start [$MODE]"
echo "================================================"

command -v python3 >/dev/null 2>&1 || { echo "[ERROR] 未找到 python3，请先安装 Python 3.10+"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "[ERROR] 未找到 node，请先安装 Node.js 18+"; exit 1; }

mkdir -p .run

# ---- [1/4] 后端依赖 -> vendor（不污染系统） ----
if [ ! -d backend/vendor/httpx ]; then
  echo "[1/4] 安装后端依赖到 backend/vendor ..."
  (cd backend && python3 -m pip install --target=vendor -r requirements.txt \
     && python3 -m pip install --target=vendor bandit dlint mitmproxy bcrypt jinja2)
else
  echo "[1/4] 后端依赖 OK"
fi

# ---- [2/4] .env ----
if [ ! -f backend/.env ]; then
  echo "[2/4] 从模板创建 backend/.env ..."
  cp backend/.env.example backend/.env
  echo "      请编辑 backend/.env 填写 LLM_API_KEY"
else
  echo "[2/4] backend/.env OK"
fi

# ---- [3/4] 前端依赖 ----
if [ ! -d frontend/node_modules ]; then
  echo "[3/4] 安装前端依赖 ..."
  (cd frontend && npm install)
else
  echo "[3/4] 前端依赖 OK"
fi

# ---- [4/4] 启动（nohup 后台运行，日志在 .run/） ----
# vendor 兜底：sitecustomize.py 通常已自动注入，这里双保险
export PYTHONPATH="$(pwd)/backend/vendor${PYTHONPATH:+:$PYTHONPATH}"

if [ "$MODE" = "prod" ]; then
  echo "[4/4] 构建前端 ..."
  (cd frontend && npm run build)
  echo "      启动后端 http://localhost:18800（托管构建产物）..."
  (cd backend && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 18800 \
      > ../.run/backend.log 2>&1 & echo $! > ../.run/backend.pid)
  sleep 6
  URL=http://localhost:18800
else
  echo "[4/4] 启动后端 + 前端开发服务器 ..."
  (cd backend && nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18800 \
      > ../.run/backend.log 2>&1 & echo $! > ../.run/backend.pid)
  (cd frontend && nohup npm run dev \
      > ../.run/frontend.log 2>&1 & echo $! > ../.run/frontend.pid)
  sleep 8
  URL=http://localhost:5173
fi

# Linux 用 xdg-open，macOS 用 open，都没有就跳过
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
fi

echo ""
echo "完成。后端 API: http://localhost:18800/docs   界面: $URL"
echo "日志: .run/backend.log / .run/frontend.log"
echo "停止: ./stop.sh"
