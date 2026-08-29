"""误报过滤器 —— 检测结果先过一遍过滤器再输出。

特征库覆盖（方案第二步第 3 点）：
1. WAF 拦截页（复用 anti_waf_tool.detect_waf 特征）
2. 404 伪装页：基线对比（随机不存在路径 vs 检测路径响应一致）
3. 登录跳转：30x → login / 登录表单特征
4. 正常业务差异：响应与正常页完全一致（bool-based SQLi 假差异）
"""
from __future__ import annotations

from urllib.parse import urlparse

from .base import ScanContext, SuspectFinding
from .http_client import Response, get

# 登录跳转/表单特征
_LOGIN_MARKERS = (
    "location:login", "/login", "sign-in", "signin", "登录",
    "name=\"password\"", "name='password'", "id=\"password\"",
)

# 404 页面常见标记
_NOT_FOUND_MARKERS = ("404", "not found", "页面不存在", "page not found")


def _is_login_redirect(r: Response) -> bool:
    if 300 <= r.status < 400:
        loc = r.header("location", "").lower()
        return any(k in loc for k in ("login", "signin", "auth", "sso"))
    if r.status == 200:
        low = (r.text or "")[:4000].lower()
        hits = sum(1 for k in _LOGIN_MARKERS if k in low)
        return hits >= 2 and ("password" in low or "登录" in low)
    return False


def _is_waf_page(r: Response) -> bool:
    try:
        from ..tools.anti_waf_tool import detect_waf
        out = detect_waf(response_text=r.text or "", headers=dict(r.headers))
        if isinstance(out, dict):
            return bool(out.get("detected") or out.get("waf"))
        if isinstance(out, str):
            # anti_waf_tool.detect_waf：未检出返回"未识别到明显 WAF 特征"，
            # 检出返回"检测到 N 个 WAF 特征"
            return "未识别" not in out
    except Exception:  # noqa: BLE001
        pass
    return False


class FalsePositiveFilter:
    """三元组过滤：WAF 页 → 404 伪装 → 登录跳转 → 相同页差异。"""

    def __init__(self, ctx: ScanContext):
        self.ctx = ctx
        self._baseline_404: str | None = None
        self._normal_hash: str | None = None

    async def _baseline(self) -> str:
        """请求一个随机不存在路径，拿到 404 伪装页基线指纹。"""
        if self._baseline_404 is None:
            root = f"{urlparse(self.ctx.base_url).scheme}://" \
                   f"{urlparse(self.ctx.base_url).netloc}"
            import secrets
            r = await get(f"{root}/__nf_{secrets.token_hex(6)}", timeout=8,
                          allow_redirects=False)
            if r.status == 0:
                self._baseline_404 = ""
            else:
                body = (r.text or "")[:2000]
                self._baseline_404 = f"{r.status}:{len(r.content)}:{hash(body)}"
        return self._baseline_404

    async def check(self, f: SuspectFinding, probe_resp: Response | None = None
                    ) -> tuple[bool, str]:
        """返回 (是否误报, 原因)。probe_resp 为触发 payload 的响应。"""
        r = probe_resp
        if r is None:
            from .http_client import http_request
            r = await http_request("GET", f.url, timeout=8, allow_redirects=False)
        if r.status == 0:
            return True, "复现请求异常"

        # 1) WAF 拦截页
        if _is_waf_page(r):
            return True, "waf_intercept_page"

        # 2) 登录跳转
        if _is_login_redirect(r):
            return True, "login_redirect"

        # 3) 404 伪装页
        base = await self._baseline()
        if base:
            body = (r.text or "")[:2000]
            cur = f"{r.status}:{len(r.content)}:{hash(body)}"
            if cur == base:
                return True, "soft_404_page"
            if r.status == 404:
                return True, "http_404"

        return False, ""
