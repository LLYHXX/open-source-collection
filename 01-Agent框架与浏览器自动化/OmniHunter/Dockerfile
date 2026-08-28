# ===== 前端构建 =====
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== 后端运行 =====
FROM python:3.12-slim
# 挖洞工具链：nmap / sqlmap（nuclei、httpx 需额外安装 go 工具，见 README）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap sqlmap curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY backend/ ./
COPY --from=frontend /frontend/dist /app/frontend/dist

RUN mkdir -p /app/data
EXPOSE 18800
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18800"]
