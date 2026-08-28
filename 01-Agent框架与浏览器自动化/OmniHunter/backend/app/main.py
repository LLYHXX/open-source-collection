"""aififteen Hunter 后端入口：FastAPI + CORS + 鉴权 + 路由 + 前端静态托管。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .core.access_control import AccessControlMiddleware
from .core.scheduler import init_scheduler, scheduler
from .database import init_db
from .routers import access as access_router
from .routers import agents as agents_router
from .routers import intel as intel_router
from .routers import reports as reports_router
from .routers import schedules as schedules_router
from .routers import settings as settings_router
from .routers import system as system_router
from .routers import tasks as tasks_router
from .routers import vulns as vulns_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_scheduler()  # 载入定时任务并启动 APScheduler
    # 预置主流 SRC 报告模板（补天/EDUSRC/漏洞盒子/CNVD/CNNVD/企业自检/通用）
    try:
        from .database import SessionLocal
        from .routers.reports import seed_preset_templates
        db = SessionLocal()
        try:
            n = seed_preset_templates(db)
            if n:
                print(f"[aififteen Hunter] 已预置 {n} 个 SRC 报告模板")
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        print(f"[aififteen Hunter] 预置模板 seed 失败（不阻塞启动）: {e}")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="aififteen Hunter", version="0.1.0", lifespan=lifespan)

# 访问控制：本地/私网 IP 免密，公网须会话(X-Access-Session)或 API Token
# 注册在 CORS 之前（内层），保证 CORS 预检 OPTIONS 不受鉴权拦截
app.add_middleware(AccessControlMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(access_router.router, prefix="/api")
app.include_router(tasks_router.router, prefix="/api")
app.include_router(agents_router.router, prefix="/api")
app.include_router(vulns_router.router, prefix="/api")
app.include_router(intel_router.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(schedules_router.router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# 前端静态托管（构建产物存在时）
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
