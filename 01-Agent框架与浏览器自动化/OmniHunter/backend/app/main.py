"""aififteen Hunter 后端入口：FastAPI + CORS + 鉴权 + 路由 + 前端静态托管。

Spec 2026-08-29 新增：
  - 统一错误码 (E-4xxx / E-5001 / E-4220) + request-id，5xx 零堆栈回显；
  - /api/health 仅返回 status；
  - FastAPI(version/docs_url) 受 api_docs_enabled Setting 控制。
"""
import logging
import secrets
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .core.access_control import AccessControlMiddleware
from .core.scheduler import init_scheduler, scheduler
from .database import init_db
from .routers import access as access_router
from .routers import agents as agents_router
from .routers import cves as cves_router
from .routers import intel as intel_router
from .routers import reports as reports_router
from .routers import schedules as schedules_router
from .routers import settings as settings_router
from .routers import system as system_router
from .routers import tasks as tasks_router
from .routers import vulns as vulns_router
from .schemas import StandardResponse

settings = get_settings()


# ===== Logging =====
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _root_logger.addHandler(_handler)
    _root_logger.setLevel(logging.INFO)

log = logging.getLogger("aififteen-hunter")


def _request_id() -> str:
    return "REQ-" + secrets.token_hex(8)


def _err(success: bool, code: str, message: str, request_id: str,
         extra: dict | None = None) -> JSONResponse:
    body = StandardResponse(
        success=success, message=message, data={"code": code, "request_id": request_id,
                                                 **(extra or {})}
    ).model_dump()
    status_map = {
        "E-5001": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "E-4220": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(code, status.HTTP_400_BAD_REQUEST)
    if code.startswith("E-4") and code != "E-4220":
        try:
            # code 形如 "E-4" + 3 位状态码（E-4404），末 3 位即 HTTP 状态
            http_status = int(code[3:6])
            if http_status < 400 or http_status > 499:
                http_status = status.HTTP_400_BAD_REQUEST
        except ValueError:
            http_status = status.HTTP_400_BAD_REQUEST
    resp = JSONResponse(status_code=http_status, content=body)
    # middleware 对异常 handler 返回的新 Response 不会再追加 header
    # （exception handler 在 middleware 栈里是 ErrorMiddleware 里的 inner 层）
    # 所以这里手动再写一次，确保响应头永远带 X-Request-Id
    resp.headers["X-Request-Id"] = request_id
    return resp


async def _500_err_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = getattr(request.state, "request_id", None) or _request_id()
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log.error("[%s] Unhandled Exception on %s %s:\n%s",
              rid, request.method, request.url.path, tb)
    return _err(False, "E-5001", "内部错误，已记录 request-id", rid)


async def _http_err_handler(request: Request, exc: HTTPException) -> JSONResponse:
    rid = getattr(request.state, "request_id", None) or _request_id()
    code = f"E-4{exc.status_code:03d}"
    # FastAPI 默认 404 = Not Found 这类 detail 是英文，可直接给用户，不泄露内部
    message = str(exc.detail) if exc.detail is not None else "请求错误"
    if exc.status_code >= 500:
        # 罕见 HTTPException(500) 走 500 档
        log.error("[%s] HTTP 5xx %s: %s", rid, request.url.path, message)
        return _err(False, "E-5001", "内部错误，已记录 request-id", rid)
    log.info("[%s] HTTP %s on %s: %s", rid, exc.status_code, request.url.path, message)
    return _err(False, code, message, rid)


async def _validation_err_handler(request: Request,
                                  exc: RequestValidationError) -> JSONResponse:
    rid = getattr(request.state, "request_id", None) or _request_id()
    # 只保留 loc 最后一段 + msg，去掉 type/url 等可能暗示内部 schema 的字段
    simple_errors = [
        {"loc": ".".join(str(x) for x in e["loc"][-2:]) if len(e.get("loc", [])) >= 2
         else str(e.get("loc", "")),
         "msg": e.get("msg", "")}
        for e in exc.errors()
    ]
    log.warning("[%s] Validation error on %s %s: %s",
                rid, request.method, request.url.path, simple_errors)
    return _err(False, "E-4220", "请求参数格式有误", rid,
                extra={"errors": simple_errors})


# ===== 动态 docs 开关 =====
def _build_app() -> FastAPI:
    docs_enabled = bool(getattr(settings, "api_docs_enabled", True))
    kwargs = dict(
        title="aififteen Hunter",
        lifespan=lifespan,
    )
    if not docs_enabled:
        kwargs.update(docs_url=None, redoc_url=None, openapi_url=None)
    # version 不挂到 FastAPI 元数据（避免 /docs 暴露），只落后端日志
    return FastAPI(**kwargs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # 全局事件循环兜底：任何游离后台任务异常都被捕获记录，不再冒泡打断进程
    try:
        from .core.bgtasks import install_loop_exception_handler
        install_loop_exception_handler()
    except Exception as e:  # noqa: BLE001
        log.warning("事件循环异常处理器安装失败（不阻塞启动）: %s", e)
    # 应用动态配置（Setting 表，优先级高于 .env）——重启后依然生效
    try:
        from .config import apply_dynamic_overrides
        from .database import SessionLocal
        from .models import Setting
        db = SessionLocal()
        try:
            from sqlalchemy import select
            overrides = {s.key: s.value for s in db.scalars(select(Setting))}
            applied = apply_dynamic_overrides(overrides)
            if applied:
                log.info("已应用 %d 项动态配置", len(applied))
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        log.warning("动态配置加载失败（不阻塞启动）: %s", e)
    # 启动期安全自检：公网令牌强度守护（仅告警，不阻塞启动）
    try:
        _tok = settings.api_token or ""
        if not _tok:
            log.warning("API_TOKEN 未设置，公网访问将仅依赖登录会话；"
                        "公网部署请设置 ≥16 位随机令牌")
        elif len(_tok) < 16:
            log.warning("API_TOKEN 强度不足（<16 位），公网部署存在被暴力猜解风险")
        else:
            log.info("安全自检通过: API_TOKEN 已配置且强度达标")
    except Exception as e:  # noqa: BLE001
        log.warning("安全自检跳过: %s", e)
    init_scheduler()  # 载入定时任务并启动 APScheduler
    # 预置主流 SRC 报告模板（补天/EDUSRC/漏洞盒子/CNVD/CNNVD/企业自检/通用）
    try:
        from .database import SessionLocal
        from .routers.reports import seed_preset_templates
        db = SessionLocal()
        try:
            n = seed_preset_templates(db)
            if n:
                log.info("已预置 %d 个 SRC 报告模板", n)
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        log.warning("预置模板 seed 失败（不阻塞启动）: %s", e)
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = _build_app()

# 统一异常处理（覆盖默认 HTML 风格错误页）
app.add_exception_handler(Exception, _500_err_handler)
app.add_exception_handler(HTTPException, _http_err_handler)
app.add_exception_handler(RequestValidationError, _validation_err_handler)


@app.middleware("http")
async def _attach_request_id(request: Request, call_next):
    request.state.request_id = _request_id()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


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
app.include_router(cves_router.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(schedules_router.router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")

# 移动靶场（安卓模拟器，可选依赖缺失时接口优雅降级）
from .routers import android as android_router  # noqa: E402
app.include_router(android_router.router, prefix="/api")

# 外接工具集成 + POC 扩展持续挖掘
from .routers import external as external_router  # noqa: E402
app.include_router(external_router.router, prefix="/api")

# Miner 路由（若存在）——延迟引入避免首次冷启动找不到模型时崩
try:
    from .routers import miner as miner_router  # noqa: E402
    app.include_router(miner_router.router, prefix="/api")
except Exception:  # noqa: BLE001
    log.info("Miner 路由未加载（首次跑，模型/setting 尚未就绪时可忽略）")


@app.get("/api/health")
def health():
    """健康检查：仅返回 status，不暴露版本、依赖或环境。"""
    return {"status": "ok"}


# 调试 boom 路由（测 E-5001 用）——仅当 miner_debug_routes=true 时挂载
def _maybe_mount_debug_boom():
    flag = False
    try:
        from .database import SessionLocal
        from .models import Setting
        db = SessionLocal()
        try:
            row = db.get(Setting, "miner_debug_routes")
            if row:
                flag = str(row.value).strip().lower() in ("1", "true", "yes", "on")
        finally:
            db.close()
    except Exception:  # noqa: BLE001
        flag = False
    # Setting 表未设置（首次冷启动）回落环境变量
    if not flag:
        try:
            flag = bool(getattr(get_settings(), "miner_debug_routes", False))
        except Exception:  # noqa: BLE001
            flag = False
    if not flag:
        return

    @app.get("/api/_dbg_boom")
    def _dbg_boom():  # pragma: no cover - 测试用
        raise RuntimeError("boom internal debug only")


_maybe_mount_debug_boom()


# 前端静态托管（构建产物存在时）
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
