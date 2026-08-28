"""鉴权与基础安全：token 校验（借鉴 AutoHunter 的多角色访问令牌）。

访问控制分层：
  1) 本地/私网 IP → 免密放行（check_access 判定）
  2) 公网 + 有效会话(X-Access-Session) → 免 token 放行
  3) 公网 + API Token(Authorization: Bearer) → 校验 settings.api_token
  4) 公网 + 无会话无 token → 401（公网需登录）

未配置 API_TOKEN 且非本地/无会话时，公网访问将被拒绝（需先设密码登录）。
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings
from .core.access_control import check_access

_bearer = HTTPBearer(auto_error=False)


async def verify_token(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
):
    # 本地IP或有效会话 → 放行（无需 API Token）
    if check_access(request):
        return "access_granted"
    # 公网访问 → 校验 API Token
    settings = get_settings()
    token = settings.api_token
    if not token:
        # 未设 API Token 且非本地/无会话 → 公网需登录
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="访问需要登录"
        )
    if not cred or cred.credentials != token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="无效或缺失访问令牌"
        )
    return cred.credentials
