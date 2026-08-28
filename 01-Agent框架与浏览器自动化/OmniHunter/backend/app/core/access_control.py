"""访问控制中间件 + 共享判定函数。

本地/私网 IP 免密；公网 IP 须有效会话(X-Access-Session)或 API Token。

设计要点：
  - 中间件在路由前拦截，公网未授权直接返回 401（覆盖所有 /api 路径，
    即使某 router 未挂 verify_token 也兜底）
  - verify_token 复用 check_access 做自主判定，即使中间件未生效也能兜底
  - 不信任 X-Forwarded-For：直接读 Request.client.host，防止公网伪造头绕过

本地/私网段：127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16、
            IPv6 ::1 与 fc00::/7（由 ipaddress.is_loopback/is_private 覆盖）。
"""
import ipaddress
import secrets
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings
from ..database import SessionLocal
from ..models import Setting

# 会话有效期 7 天（与 routers/access._SESSION_TTL 保持一致）
_SESSION_TTL = 7 * 24 * 3600
# 放行路径前缀：健康检查、access 端点；非 /api 路径（前端静态资源）也放行
_PUBLIC_PREFIXES = ("/api/health", "/api/access")


def is_local_ip(ip: str) -> bool:
    """判断是否本地回环或私网 IP。"""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # 解析失败按非本地处理（保守）
        return False
    return addr.is_loopback or addr.is_private


def get_client_ip(request: Request) -> str:
    """获取真实客户端 IP。

    - 默认（无受信代理）：直接返回 request.client.host，不信任
      X-Forwarded-For，防止公网伪造头绕过本地判定。
    - 反向代理部署（trusted_proxies 已配置）：若直连对端为受信代理，
      则从 X-Forwarded-For 取最左端原始客户端 IP，避免代理 IP 被误判
      为本地导致公网请求绕过密码保护。
    """
    client = request.client.host if request.client else "0.0.0.0"
    trusted = get_settings().trusted_proxy_list
    if trusted and client in trusted:
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            # 取最左端（原始客户端）；多级代理需按信任深度取
            return xff.split(",")[0].strip()
    return client


def _get_setting_value(key: str) -> str:
    """中间件无法用 Depends(get_db)，直接开短会话读 Setting。"""
    db = SessionLocal()
    try:
        s = db.get(Setting, key)
        return s.value if s else ""
    finally:
        db.close()


def validate_session(token: str) -> bool:
    """校验会话令牌：存在 + 未过期。令牌存储格式为 token|expire_ts。"""
    if not token:
        return False
    raw = _get_setting_value("access_session")
    if not raw or "|" not in raw:
        return False
    stored_token, _, expire_str = raw.partition("|")
    # 常量时间比较，防时序攻击推测会话令牌
    if not secrets.compare_digest(stored_token, token):
        return False
    try:
        return time.time() < float(expire_str)
    except ValueError:
        return False


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def check_access(request: Request) -> bool:
    """自主判定：本地IP或有效会话则放行（供 verify_token 复用）。

    注意：此处不校验 API Token（由 verify_token 的 bearer 分支处理），
    仅判定「本地或会话」两种免 token 场景。
    """
    if is_local_ip(get_client_ip(request)):
        return True
    session = request.headers.get("X-Access-Session", "")
    return validate_session(session)


class AccessControlMiddleware(BaseHTTPMiddleware):
    """公网访问密码保护中间件。

    - 本地/私网 IP：免密放行
    - 公网 IP：须有效会话(X-Access-Session) 或 API Token(Authorization: Bearer)
    - 健康检查 / access 端点 / 前端静态资源：始终放行
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # 健康检查 / access 端点 / 非 /api 路径（前端静态资源）→ 放行
        if path.startswith(_PUBLIC_PREFIXES) or not path.startswith("/api"):
            return await call_next(request)

        client_ip = get_client_ip(request)
        # 本地/私网 → 免密放行
        if is_local_ip(client_ip):
            return await call_next(request)
        # 公网 → 校验会话
        if validate_session(request.headers.get("X-Access-Session", "")):
            return await call_next(request)
        # 公网 → 校验 API Token（兼容程序化访问，常量时间比较防时序攻击）
        bearer = _extract_bearer_token(request)
        settings = get_settings()
        if bearer and settings.api_token and secrets.compare_digest(bearer, settings.api_token):
            return await call_next(request)
        # 公网未授权 → 401
        return JSONResponse(
            {"detail": "访问需要登录，请先通过密码验证"},
            status_code=401,
        )
