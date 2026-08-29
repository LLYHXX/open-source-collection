"""auth_traverse —— 越权检测确定性模块（方案第二步第 1 点）。

自动提取页面所有接口，分别用「管理员、普通用户、未登录」三个身份发请求，
对比响应体/状态码/数据量差异，超阈值判定越权：
- 垂直越权：user 能访问 admin-only 接口（admin 2xx 且数据量相近）
- 未授权访问：anonymous 能访问需登录接口（user 2xx 且 anon 内容相近）

身份凭据从 ctx.extra["sessions"] 注入，格式：
  {"admin": {"cookie": "k=v; k2=v2"}, "user": {...}, "anon": {}}
缺省身份自动降级（admin/user 缺失则只测未授权访问）。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from urllib.parse import urljoin, urlparse

from ..base import ScanContext, SuspectFinding
from ..http_client import extract_links, http_request

# 常见需登录接口字典（补充首页提取不到的场景）
_AUTH_ENDPOINTS = (
    "/user/info", "/user/profile", "/api/user/info", "/api/user",
    "/admin/list", "/admin/users", "/api/admin/users", "/api/admin",
    "/order/list", "/api/orders", "/api/order/list",
    "/api/me", "/api/profile", "/member/index", "/manage/user/list",
)

# 管理端特征（命中则视为 admin-only 接口）
_ADMIN_HINTS = ("admin", "manage", "console", "system", "audit")


@dataclass
class IdentitySession:
    name: str
    cookie: str = ""
    headers: dict = field(default_factory=dict)

    def to_headers(self) -> dict:
        h = dict(self.headers)
        if self.cookie:
            h["Cookie"] = self.cookie
        return h


@dataclass
class ProbeResult:
    url: str
    status: int
    length: int
    body_hash: str
    is_login_redirect: bool = False


def extract_endpoints(ctx: ScanContext) -> list[str]:
    """从首页/指纹路径提取接口清单，合并常见接口字典。"""
    endpoints: list[str] = []
    for p in ctx.fp.paths:
        if not re.search(r"\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$", p, re.I):
            endpoints.append(urljoin(ctx.base_url, p))
    for e in _AUTH_ENDPOINTS:
        endpoints.append(urljoin(ctx.base_url, e))
    # 去重保序
    seen: set[str] = set()
    out = []
    for e in endpoints:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out[:60]


def _is_admin_path(url: str) -> bool:
    low = url.lower()
    return any(h in low for h in _ADMIN_HINTS)


async def _probe(url: str, sess: IdentitySession) -> ProbeResult:
    r = await http_request("GET", url, headers=sess.to_headers(), timeout=10,
                           allow_redirects=False)
    body = r.text or ""
    redirect = (300 <= r.status < 400 and
                "login" in r.header("location", "").lower()) or \
               (r.status == 200 and 'name="password"' in body.lower())
    return ProbeResult(
        url=url, status=r.status, length=len(r.content),
        body_hash=hashlib.md5(body[:8000].encode("utf-8", "ignore")).hexdigest(),
        is_login_redirect=redirect,
    )


def _looks_same(a: ProbeResult, b: ProbeResult) -> bool:
    """两个身份响应是否实质相同（可访问且内容相近）。"""
    if not (200 <= a.status < 300 and 200 <= b.status < 300):
        return False
    if a.body_hash == b.body_hash:
        return True
    # 内容长度相近（±15%）且都不是空页
    if a.length > 0 and b.length > 0:
        ratio = min(a.length, b.length) / max(a.length, b.length)
        return ratio >= 0.85
    return False


async def run_auth_traverse(ctx: ScanContext,
                            findings: list[SuspectFinding]) -> None:
    """执行三身份越权遍历，疑似结果 append 到 findings。"""
    sessions = ctx.extra.get("sessions") or {}
    admin = IdentitySession("admin", **(sessions.get("admin") or
                                        {"cookie": sessions.get("admin_cookie", "")}))
    user = IdentitySession("user", **(sessions.get("user") or
                                      {"cookie": sessions.get("user_cookie", "")}))
    anon = IdentitySession("anon")

    endpoints = extract_endpoints(ctx)
    if not endpoints:
        return

    for url in endpoints:
        u_res = await _probe(url, user)
        if u_res.is_login_redirect or u_res.status in (401, 403):
            pass  # user 被拦，检查 anon 是否反而能进
        else:
            a_res = await _probe(url, admin)
            # 垂直越权：user 与 admin 访问 admin-only 接口内容相近
            if _is_admin_path(url) and _looks_same(u_res, a_res):
                findings.append(SuspectFinding(
                    plugin_id="auth_traverse.vertical",
                    vuln_type="unauthorized_access",
                    title=f"疑似垂直越权：普通用户可访问管理接口 {urlparse(url).path}",
                    detail=(
                        f"接口 {url} 具有管理端特征，普通用户身份与管理员身份"
                        f"响应均为 2xx 且内容相近（user len={u_res.length}, "
                        f"admin len={a_res.length}），疑似缺少角色校验。"
                    ),
                    payload=f"GET {url} (user session)",
                    evidence=f"user: {u_res.status}/{u_res.length}B; "
                             f"admin: {a_res.status}/{a_res.length}B",
                    url=url, vector="AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
                    confidence=0.7,
                ))

        # 未授权访问：user 可访问而 anonymous 内容相近
        n_res = await _probe(url, anon)
        if (not n_res.is_login_redirect and n_res.status not in (401, 403)
                and u_res.status not in (401, 403)
                and not u_res.is_login_redirect
                and _looks_same(u_res, n_res)
                and u_res.length > 200):
            findings.append(SuspectFinding(
                plugin_id="auth_traverse.anon",
                vuln_type="unauthorized_access",
                title=f"疑似未授权访问：未登录可直接访问 {urlparse(url).path}",
                detail=(
                    f"接口 {url} 登录用户与未登录匿名访问响应均为 2xx 且内容相近"
                    f"（user len={u_res.length}, anon len={n_res.length}），"
                    f"疑似缺少认证校验。"
                ),
                payload=f"GET {url} (anonymous)",
                evidence=f"user: {u_res.status}/{u_res.length}B; "
                         f"anon: {n_res.status}/{n_res.length}B",
                url=url, vector="AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N",
                confidence=0.65,
            ))


async def verify_auth_finding(ctx: ScanContext,
                              finding: SuspectFinding) -> SuspectFinding | None:
    """越权独立复现：再发一轮匿名/用户请求，结论一致才算确认。"""
    url = finding.url
    user = IdentitySession("user", **((ctx.extra.get("sessions") or {})
                                      .get("user") or {}))
    u1 = await _probe(url, user)
    n1 = await _probe(url, IdentitySession("anon"))
    same = _looks_same(u1, n1)
    # vertical 类复核 user 是否仍可访问 admin 接口
    if finding.plugin_id == "auth_traverse.vertical":
        if 200 <= u1.status < 300 and not u1.is_login_redirect:
            finding.verified = True
            finding.verify_evidence = f"复现: user 再访 {url} -> {u1.status}/{u1.length}B"
            finding.confidence = min(0.9, finding.confidence + 0.15)
            return finding
        return None
    # anon 类：二次匿名访问仍 2xx 且与 user 相近
    if finding.plugin_id == "auth_traverse.anon":
        if same and u1.length > 200:
            finding.verified = True
            finding.verify_evidence = (f"复现: anon 再访 {url} -> "
                                       f"{n1.status}/{n1.length}B 与 user 相近")
            finding.confidence = min(0.9, finding.confidence + 0.15)
            return finding
    return None
