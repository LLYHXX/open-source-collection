"""访问控制路由：首次设密码 / 登录 / 登出 / 状态查询。

端点：
  GET  /access/status  返回是否已设密码（前端据此显示「设置」或「登录」）
  POST /access/setup   首次设密码（已设则 409 防覆盖），成功后直接签发会话
  POST /access/login   密码校验，签发 7 天会话；内存级 IP 限流 5 次/分钟
  POST /access/logout  清除当前会话

密码用 bcrypt 哈希（vendor 已提供），会话令牌 secrets.token_urlsafe(32)。
"""
import secrets
import time
from collections import deque

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.access_control import validate_session
from ..database import get_db
from ..models import Setting

router = APIRouter(prefix="/access", tags=["access"])

_SESSION_TTL = 7 * 24 * 3600  # 会话有效期 7 天
_BCRYPT_COST = 12
_BCRYPT_MAX_BYTES = 72  # bcrypt 密码输入上限 72 字节
_RATE_WINDOW = 60  # 限流窗口 60s
_RATE_MAX = 5  # 每窗口最多 5 次失败/成功均计数
_RATE_DICT_MAX = 10000  # 限流字典上限，防公网暴露后内存无限增长
_login_attempts: dict[str, deque] = {}


def _pwd_bytes(pwd: str) -> bytes:
    """编码并截断到 bcrypt 72 字节上限，避免长/中文密码触发 500。

    截断在多字节字符边界上可能不完整，但同一输入始终产生相同哈希，
    setup 与 login 两端一致即可正确校验。
    """
    return (pwd or "").encode("utf-8")[:_BCRYPT_MAX_BYTES]


def _get_setting(db: Session, key: str) -> str:
    s = db.get(Setting, key)
    return s.value if s else ""


def _set_setting(db: Session, key: str, value: str) -> None:
    s = db.get(Setting, key)
    if not s:
        s = Setting(key=key, value=value)
        db.add(s)
    else:
        s.value = value
    db.commit()


def _issue_session(db: Session) -> str:
    """签发会话令牌，存 Setting(access_session)=token|expire_ts。"""
    token = secrets.token_urlsafe(32)
    _set_setting(db, "access_session", f"{token}|{time.time() + _SESSION_TTL}")
    return token


class PasswordIn(BaseModel):
    password: str


class StatusOut(BaseModel):
    password_set: bool


class SessionOut(BaseModel):
    session_token: str
    expires_in: int


class MessageOut(BaseModel):
    message: str


@router.get("/status", response_model=StatusOut)
def get_status(db: Session = Depends(get_db)):
    """查询是否已设密码。前端据此决定显示「设置密码」或「登录」。"""
    return StatusOut(password_set=bool(_get_setting(db, "access_password_hash")))


@router.post("/setup", response_model=SessionOut)
def setup_password(payload: PasswordIn, db: Session = Depends(get_db)):
    """首次设置访问密码。已设则 409 拒绝（防止覆盖）。"""
    if _get_setting(db, "access_password_hash"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "密码已设置，如需重置请清空 settings 表 access_password_hash 后重启",
        )
    pwd = (payload.password or "").strip()
    if len(pwd) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "密码至少 6 位")
    hashed = bcrypt.hashpw(_pwd_bytes(pwd), bcrypt.gensalt(_BCRYPT_COST))
    _set_setting(db, "access_password_hash", hashed.decode("utf-8"))
    token = _issue_session(db)
    return SessionOut(session_token=token, expires_in=_SESSION_TTL)


@router.post("/login", response_model=SessionOut)
def login(payload: PasswordIn, request: Request, db: Session = Depends(get_db)):
    """密码登录，签发会话令牌。带 IP 级限流防爆破。"""
    ip = request.client.host if request.client else "_global"
    now = time.time()
    dq = _login_attempts.get(ip)
    if dq is not None:
        while dq and now - dq[0] > _RATE_WINDOW:
            dq.popleft()
        if not dq:
            # 清理空 deque 的 key，防止公网暴露后 dict 无限增长（内存泄漏）
            del _login_attempts[ip]
            dq = None
    if dq is None:
        # 字典超上限时整体清空，防大量不同 IP 撑爆内存
        if len(_login_attempts) >= _RATE_DICT_MAX:
            _login_attempts.clear()
        dq = _login_attempts[ip] = deque()
    if len(dq) >= _RATE_MAX:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "尝试过于频繁，请稍后再试"
        )
    dq.append(now)

    stored = _get_setting(db, "access_password_hash")
    if not stored:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "尚未设置密码，请先初始化")
    try:
        ok = bcrypt.checkpw(_pwd_bytes(payload.password or ""), stored.encode("utf-8"))
    except ValueError:
        ok = False
    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "密码错误")
    token = _issue_session(db)
    return SessionOut(session_token=token, expires_in=_SESSION_TTL)


@router.post("/logout", response_model=MessageOut)
def logout(request: Request, db: Session = Depends(get_db)):
    """注销当前会话。

    需携带有效会话令牌(X-Access-Session)才允许登出，防止未认证者
    清空他人会话造成强制重新登录的 DoS。
    """
    presented = request.headers.get("X-Access-Session", "")
    if not validate_session(presented):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无有效会话")
    _set_setting(db, "access_session", "")
    return MessageOut(message="已登出")
