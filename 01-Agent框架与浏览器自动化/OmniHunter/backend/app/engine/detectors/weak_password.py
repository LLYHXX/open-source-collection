"""弱口令检测插件 —— 常见登录端点弱口令组合（有副作用，默认关闭）。"""
from __future__ import annotations

import re

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request, get
from urllib.parse import urljoin, urlparse

_LOGIN_PATHS = (
    "/login", "/admin/login", "/user/login", "/api/login", "/auth/login",
    "/manage/login", "/system/login", "/signin", "/admin/signin",
)

# 每端点最多尝试的弱口令组合（控制副作用）
_WEAK_CREDS = (
    ("admin", "admin"), ("admin", "123456"), ("admin", "admin123"),
    ("test", "test"), ("root", "root"),
)

# 登录成功特征
_SUCCESS_SIGS = re.compile(
    r"(logout|退出登录|欢迎|welcome|dashboard|token|home)", re.I)
_FAIL_SIGS = re.compile(
    r"(密码错误|用户名或密码|incorrect|invalid|failed|error|失败)", re.I)

_USER_FIELD_NAMES = ("username", "user", "account", "login", "email", "name")
_PASS_FIELD_NAMES = ("password", "passwd", "pwd", "pass")


class WeakPasswordPlugin(DetectorPlugin):
    id = "weakpwd.common_creds"
    vuln_type = "weak_password"
    name = "弱口令"
    description = "常见登录端点尝试有限弱口令组合（每端点≤5 组，控制副作用）"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    side_effect_free = False

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        parsed = urlparse(ctx.base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"

        paths = list(_LOGIN_PATHS)
        for p in ctx.fp.paths:
            if "login" in p.lower() or "signin" in p.lower():
                paths.insert(0, p)

        for path in paths[:5]:
            url = urljoin(root, path)
            page = await get(url, timeout=8)
            if page.status != 200 or not page.text:
                continue
            # 解析表单字段名
            user_field = self._find_field(page.text, _USER_FIELD_NAMES)
            pass_field = self._find_field(page.text, _PASS_FIELD_NAMES)
            if not pass_field:
                continue
            user_field = user_field or "username"

            for username, password in _WEAK_CREDS:
                r = await http_request(
                    "POST", url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data=f"{user_field}={username}&{pass_field}={password}",
                    timeout=8, allow_redirects=True)
                if r.status == 0:
                    break
                body = r.text or ""
                ok = (r.status == 200 and _SUCCESS_SIGS.search(body[:5000])
                      and not _FAIL_SIGS.search(body[:5000]))
                # 跟随重定向后离开 login 路径也算成功
                if not ok and r.ok and "login" not in (r.url or "").lower():
                    ok = True
                if ok:
                    findings.append(SuspectFinding(
                        plugin_id=self.id, vuln_type=self.vuln_type,
                        title=f"弱口令：{path} ({username}/{password})",
                        detail=(f"登录端点 {path} 存在弱口令 {username}/{password}，"
                                f"登录响应命中成功特征且无失败提示。"),
                        payload=f"{username}/{password}",
                        evidence=f"POST {url} -> {r.status}, 响应含成功特征",
                        url=url, param=f"{user_field},{pass_field}",
                        vector=self.default_vector, confidence=0.7,
                    ))
                    break  # 该端点命中即止，减少副作用
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        import asyncio
        await asyncio.sleep(1.0)
        creds = finding.payload.split("/", 1)
        if len(creds) != 2:
            return None
        user_field, pass_field = (finding.param.split(",") + ["username", "password"])[:2]
        r = await http_request(
            "POST", finding.url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"{user_field}={creds[0]}&{pass_field}={creds[1]}",
            timeout=8)
        if r.status and _SUCCESS_SIGS.search((r.text or "")[:5000]):
            finding.verified = True
            finding.verify_evidence = f"复现: {creds[0]}/{creds[1]} 二次登录成功特征命中"
            finding.confidence = min(0.9, finding.confidence + 0.12)
            return finding
        return None

    @staticmethod
    def _find_field(html: str, names: tuple) -> str | None:
        import re as _re
        for m in _re.finditer(
                r'<input[^>]*name\s*=\s*["\']([^"\']+)["\']', html, _re.I):
            if m.group(1).lower() in names:
                return m.group(1)
        return None
