"""权限发现专项 Agent（单站协作核心模块）。

用户需求：「单站协作 — 都有什么权限？让 agent 自己自动挖掘」

本 Agent 对一个站点执行 5 类权限检测：
  1) 未授权访问：匿名身份可访问需登录接口
  2) 水平越权：普通用户 A 能访问用户 B 的数据（IDOR + 业务隔离缺失）
  3) 垂直越权：普通用户能访问管理接口
  4) IDOR：ID 参数无归属校验
  5) 权限矩阵：以矩阵形式输出每身份对每端点的访问能力

复用引擎层确定性模块：
  - engine.logic.auth_traverse（三身份越权遍历，需 sessions）
  - engine.logic.idor_traverse（ID 枚举遍历）
  - engine.http_client（统一异步 HTTP，不抛异常）

输入：task_input = {
    "url": "https://target.com",
    "site_profile": {...},     # 来自 SiteProfilerAgent
    "sessions": {
        "admin": {"cookie": "..."},
        "user": {"cookie": "..."},
        "user2": {"cookie": "..."},   # 第二个普通用户身份（用于水平越权）
    },
    "anon_probe": True,         # 是否测未授权
}
输出：{
    "permission_matrix": [{"endpoint": ..., "admin": "allow", "user": "allow",
                            "anon": "allow", "suspected": ["未授权", ...]}],
    "vulns": [{vuln_type, title, detail, payload, evidence, ...}],
    "endpoints": [...],
}
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry
from ..engine.http_client import http_request


# 常见需登录/管理端接口字典（补充首页提取不到的场景）
_AUTH_ENDPOINTS = (
    "/user/info", "/user/profile", "/api/user/info", "/api/user",
    "/admin/list", "/admin/users", "/api/admin/users", "/api/admin",
    "/order/list", "/api/orders", "/api/order/list",
    "/api/me", "/api/profile", "/member/index", "/manage/user/list",
    "/api/v1/users", "/api/v1/admin", "/api/account/info",
)

# 管理端特征（命中则视为 admin-only 接口）
_ADMIN_HINTS = ("admin", "manage", "console", "system", "audit", "root")

# 静态资源扩展名（提取接口时过滤）
_STATIC_EXT = re.compile(r"\.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?|ttf|map)$", re.I)


def _looks_admin(url: str) -> bool:
    low = url.lower()
    return any(h in low for h in _ADMIN_HINTS)


def _body_sig(text: str) -> str:
    """响应体签名：MD5 前 8000 字符。"""
    return hashlib.md5((text or "")[:8000].encode("utf-8", "ignore")).hexdigest()


def _looks_same(a_status: int, a_len: int, a_sig: str,
                b_status: int, b_len: int, b_sig: str) -> bool:
    """两个身份响应是否实质相同（可访问且内容相近）。"""
    if not (200 <= a_status < 300 and 200 <= b_status < 300):
        return False
    if a_sig == b_sig:
        return True
    # 内容长度相近（±15%）且都不是空页
    if a_len > 0 and b_len > 0:
        ratio = min(a_len, b_len) / max(a_len, b_len)
        return ratio >= 0.85
    return False


def _is_login_redirect(status: int, location: str, body: str) -> bool:
    """登录重定向判定。"""
    if 300 <= status < 400 and "login" in (location or "").lower():
        return True
    if status == 200 and 'name="password"' in (body or "").lower():
        return True
    return False


async def _probe(url: str, headers: dict | None = None,
                 timeout: int = 10) -> dict:
    """探测一个 URL，返回 {status, length, sig, is_login_redirect, location}。

    使用 engine.http_client.http_request：永不抛异常，失败 status=0。
    """
    r = await http_request("GET", url, headers=headers or {}, timeout=timeout,
                           allow_redirects=False)
    body = r.text or ""
    return {
        "status": r.status,
        "length": len(r.content),
        "sig": _body_sig(body),
        "is_login_redirect": _is_login_redirect(r.status,
                                                r.header("location", ""), body),
        "location": r.header("location", ""),
        "body_snippet": body[:500],
    }


class PermissionAgent(BaseAgent):
    role = "permission"
    description = ("权限发现专项：未授权访问 / 水平越权 / 垂直越权 / IDOR / "
                   "权限矩阵，复用 auth_traverse + idor_traverse 确定性逻辑。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router=None, pruning=None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event,
                         router=router, pruning=pruning)

    async def run(self, task_input: dict) -> dict:
        url = (task_input.get("url") or
               (self.target.url if self.target else ""))
        if not url:
            return {"vulns": [], "permission_matrix": [], "endpoints": []}

        site_profile = task_input.get("site_profile") or {}
        sessions = task_input.get("sessions") or {}
        anon_probe = task_input.get("anon_probe", True)

        self.think(f"权限发现专项启动: {url}, 身份数={len(sessions) + 1}, "
                    f"anon_probe={anon_probe}")

        # 1) 提取接口清单
        endpoints = self._collect_endpoints(url, site_profile)
        if not endpoints:
            self.think("无可用接口，跳过权限发现")
            return {"vulns": [], "permission_matrix": [], "endpoints": []}
        self.think(f"收集到 {len(endpoints)} 个待测接口")

        # 2) 构造身份列表
        identities = self._build_identities(sessions, anon_probe)

        # 3) 三身份越权遍历 + 权限矩阵
        matrix: list[dict] = []
        vulns: list[dict] = []
        for ep in endpoints:
            row = await self._probe_endpoint(ep, identities)
            matrix.append(row)
            # 检测疑似漏洞
            v_list = self._detect_vulns(ep, row, identities)
            vulns.extend(v_list)

        # 4) IDOR 检测（对所有接口的 ID 参数做变异）
        idor_vulns = await self._run_idor_check(endpoints, sessions)
        vulns.extend(idor_vulns)

        self.think(f"权限发现完成: 矩阵 {len(matrix)} 行，疑似漏洞 {len(vulns)} 条")

        # 5) LLM 兜底：对疑似漏洞做去误报（router 规则层 0 Token 预筛，未命中再走大模型）
        if vulns and self.router:
            try:
                vulns = self.router.dispatch("filter_false_positives", vulns) or vulns
            except Exception:  # noqa: BLE001 router 未实现该方法时直接跳过
                pass

        return {
            "permission_matrix": matrix,
            "vulns": vulns,
            "endpoints": endpoints,
        }

    def _collect_endpoints(self, base_url: str, site_profile: dict) -> list[str]:
        """从首页/指纹/site_profile 提取接口清单 + 常见接口字典。"""
        endpoints: list[str] = []

        # site_profile.discovered_urls（来自 SiteProfiler 的规则层 URL 提取）
        for u in (site_profile.get("discovered_urls") or [])[:30]:
            if u and not _STATIC_EXT.search(u):
                endpoints.append(u if u.startswith("http")
                                 else urljoin(base_url, u))

        # site_profile.web_entries（httpx 探活结果）
        for entry in (site_profile.get("web_entries") or [])[:10]:
            if isinstance(entry, str):
                endpoints.append(entry if entry.startswith("http")
                                 else urljoin(base_url, entry))

        # 常见需登录/管理接口字典
        for e in _AUTH_ENDPOINTS:
            endpoints.append(urljoin(base_url, e))

        # 去重保序
        seen: set[str] = set()
        out = []
        for e in endpoints:
            if e not in seen:
                seen.add(e)
                out.append(e)
        # 限制单站接口数避免无限增长
        return out[:60]

    def _build_identities(self, sessions: dict, anon_probe: bool) -> list[dict]:
        """构造身份列表：admin/user/user2/anon。"""
        identities: list[dict] = []
        for name in ("admin", "user", "user2"):
            s = sessions.get(name) or {}
            if isinstance(s, dict) and (s.get("cookie") or s.get("headers")):
                identities.append({
                    "name": name,
                    "headers": self._build_session_headers(s),
                })
        if anon_probe:
            identities.append({"name": "anon", "headers": {}})
        return identities

    def _build_session_headers(self, sess: dict) -> dict:
        """session dict → HTTP headers。"""
        h = dict(sess.get("headers") or {})
        cookie = sess.get("cookie", "")
        if cookie:
            h["Cookie"] = cookie
        token = sess.get("token", "")
        if token:
            h["Authorization"] = f"Bearer {token}" if token and " " not in token else token
        return h

    async def _probe_endpoint(self, url: str, identities: list[dict]) -> dict:
        """对单个接口跑所有身份，构造权限矩阵行。"""
        row: dict = {"endpoint": url, "is_admin_path": _looks_admin(url)}
        for ident in identities:
            result = await _probe(url, ident["headers"])
            row[ident["name"]] = {
                "status": result["status"],
                "length": result["length"],
                "sig": result["sig"],
                "allow": (200 <= result["status"] < 300
                          and not result["is_login_redirect"]),
                "is_login_redirect": result["is_login_redirect"],
            }
        # 推断 suspected 列表（具体检测在 _detect_vulns）
        row["suspected"] = []
        return row

    def _detect_vulns(self, url: str, row: dict, identities: list[dict]) -> list[dict]:
        """从权限矩阵行检测疑似漏洞。"""
        vulns: list[dict] = []
        admin_info = row.get("admin") or {}
        user_info = row.get("user") or {}
        anon_info = row.get("anon") or {}

        # 1) 未授权访问：anon 可访问需登录接口
        if (user_info.get("allow") and anon_info.get("allow")
                and user_info.get("length", 0) > 200
                and _looks_same(user_info.get("status", 0),
                                user_info.get("length", 0),
                                user_info.get("sig", ""),
                                anon_info.get("status", 0),
                                anon_info.get("length", 0),
                                anon_info.get("sig", ""))):
            vulns.append(self._mk_vuln(
                "unauthorized_access",
                f"疑似未授权访问：未登录可访问 {urlparse(url).path}",
                f"接口 {url} 登录用户与未登录匿名访问响应均为 2xx 且内容相近"
                f"（user len={user_info.get('length', 0)}, "
                f"anon len={anon_info.get('length', 0)}），"
                f"疑似缺少认证校验。",
                f"GET {url} (anonymous)",
                f"user: {user_info.get('status', 0)}/{user_info.get('length', 0)}B; "
                f"anon: {anon_info.get('status', 0)}/{anon_info.get('length', 0)}B",
                url, severity="high", confidence=0.7))
            row["suspected"].append("未授权访问")

        # 2) 垂直越权：user 可访问 admin-only 接口
        if (row.get("is_admin_path") and user_info.get("allow")
                and admin_info.get("allow")):
            # admin 和 user 都能 2xx 访问管理接口
            vulns.append(self._mk_vuln(
                "unauthorized_access",
                f"疑似垂直越权：普通用户可访问管理接口 {urlparse(url).path}",
                f"接口 {url} 具有管理端特征，普通用户身份与管理员身份"
                f"响应均为 2xx（user len={user_info.get('length', 0)}, "
                f"admin len={admin_info.get('length', 0)}），"
                f"疑似缺少角色校验。",
                f"GET {url} (user session)",
                f"user: {user_info.get('status', 0)}/{user_info.get('length', 0)}B; "
                f"admin: {admin_info.get('status', 0)}/{admin_info.get('length', 0)}B",
                url, severity="high", confidence=0.7))
            row["suspected"].append("垂直越权")

        # 3) 水平越权（user2 维度）：user2 能访问 user 的数据
        user2_info = row.get("user2") or {}
        if (user_info.get("allow") and user2_info.get("allow")
                and user_info.get("length", 0) > 100
                and abs(user_info.get("length", 0) - user2_info.get("length", 0)) < 100):
            # user 和 user2 看到相同数据 → 缺少业务隔离
            vulns.append(self._mk_vuln(
                "unauthorized_access",
                f"疑似水平越权：两个普通用户身份访问相同数据 {urlparse(url).path}",
                f"接口 {url} 用 user 与 user2 两个身份访问响应内容相近"
                f"（user len={user_info.get('length', 0)}, "
                f"user2 len={user2_info.get('length', 0)}），"
                f"疑似缺少业务数据归属校验。",
                f"GET {url} (user2 session)",
                f"user: {user_info.get('status', 0)}/{user_info.get('length', 0)}B; "
                f"user2: {user2_info.get('status', 0)}/{user2_info.get('length', 0)}B",
                url, severity="medium", confidence=0.6))
            row["suspected"].append("水平越权")

        return vulns

    async def _run_idor_check(self, endpoints: list[str],
                               sessions: dict) -> list[dict]:
        """IDOR 检测：对所有接口的 ID 参数做变异遍历。"""
        from urllib.parse import parse_qsl, urlencode, urlunparse

        vulns: list[dict] = []
        user_sess = sessions.get("user") or {}
        user_headers = self._build_session_headers(user_sess)

        for url in endpoints[:15]:  # 限制 IDOR 检测接口数避免过慢
            parsed = urlparse(url)
            qs = parse_qsl(parsed.query, keep_blank_values=True)
            # 找 ID 类参数
            id_params = [(k, v) for k, v in qs
                         if self._is_id_param(k, v)]
            if not id_params:
                continue

            # 基线
            base_r = await _probe(url, user_headers)
            if not (200 <= base_r["status"] < 300):
                continue

            for param, value in id_params:
                for delta in (1, -1, 2):
                    new_val = self._mutate_id(value, delta)
                    if not new_val or new_val == value:
                        continue
                    new_qs = [(k, new_val if k == param else v) for k, v in qs]
                    probe_url = urlunparse(parsed._replace(query=urlencode(new_qs)))
                    r = await _probe(probe_url, user_headers)
                    if not (200 <= r["status"] < 300):
                        continue
                    # 命中：响应包含新 ID 且内容与基线不同
                    body = r["body_snippet"]
                    if (new_val.lower() in body.lower()
                            and abs(r["length"] - base_r["length"]) > 50):
                        vulns.append(self._mk_vuln(
                            "idor",
                            f"疑似 IDOR：{param}={value} 可遍历访问 {param}={new_val}",
                            f"接口 {url} 的 ID 参数 {param} 未做归属校验："
                            f"将 {param} 改为 {new_val} 后仍返回 2xx，"
                            f"且响应内容包含新 ID 值，可水平越权读取他人数据。",
                            f"{param}={new_val}",
                            f"baseline {base_r['status']}/{base_r['length']}B; "
                            f"mutated {r['status']}/{r['length']}B "
                            f"(含 {param}={new_val})",
                            probe_url, severity="high", confidence=0.7))
                        break  # 该参数命中一次即够

        return vulns

    def _is_id_param(self, name: str, value: str) -> bool:
        """判断参数是否为 ID 类。"""
        name_low = name.lower()
        if any(k in name_low for k in ("id", "uid", "oid", "no", "num")):
            return True
        # 纯数字或 UUID
        if re.fullmatch(r"\d{1,10}", value):
            return True
        if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        value, re.I):
            return True
        return False

    def _mutate_id(self, value: str, delta: int) -> str | None:
        """ID 变异：数值 ±delta；UUID 末段微变。"""
        if re.fullmatch(r"\d{1,10}", value):
            return str(max(1, int(value) + delta))
        m = re.fullmatch(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-)([0-9a-f]{12})",
            value, re.I)
        if m:
            tail = int(m.group(2)[:4], 16)
            new_tail = f"{(tail + delta) % 0xffff:04x}"
            return m.group(1) + new_tail + m.group(2)[4:]
        return None

    def _mk_vuln(self, vuln_type: str, title: str, detail: str,
                 payload: str, evidence: str, url: str,
                 severity: str = "medium", confidence: float = 0.6) -> dict:
        return {
            "vuln_type": vuln_type,
            "severity": severity,
            "title": title,
            "detail": detail,
            "payload": payload,
            "evidence": evidence,
            "repro": url,
            "verified": False,  # 待 Verifier 独立复现
            "confidence": confidence,
        }
