"""SSRF 检测插件 —— 内部服务特征探测（确定性规则）。

注入回连地址到 URL/文件类参数，观察响应是否包含内部服务指纹。
默认使用目标自身回环地址（不依赖外部 DNSLog，合规且无外联）。
"""
from __future__ import annotations

import re

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request, extract_query_params
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

# 回连地址（目标自身，不外联）
_CALLBACK_URLS = (
    "http://127.0.0.1:80", "http://localhost:8080",
    "http://127.0.0.1:6379",  # Redis
)
# 内部服务响应指纹
_INTERNAL_SIGS = {
    "redis": re.compile(r"-ERR|^\+PONG|\$-?\d+", re.M),
    "web": re.compile(r"<html|<title|HTTP/1\.[01] \d{3}", re.I),
}

# SSRF 候选参数名
_SSRF_PARAMS = ("url", "uri", "link", "src", "source", "target", "dest",
                "redirect", "goto", "fetch", "load", "proxy", "site", "host",
                "callback", "next", "return", "image", "file", "doc")


class SsrfPlugin(DetectorPlugin):
    id = "ssrf.internal_probe"
    vuln_type = "ssrf"
    name = "SSRF 服务端请求伪造"
    description = "URL 类参数注入回环地址，命中内部服务指纹即疑似"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []

        # 候选：URL 自带 ssrf 类参数；否则用常见参数打首页
        candidates: list[tuple[str, str]] = []
        seen = set()
        urls = [ctx.base_url] + [
            u for p in ctx.fp.paths[:10]
            if (u := self._abs(ctx.base_url, p)) and extract_query_params(u)]
        for u in urls:
            for k in extract_query_params(u):
                if k.lower() in _SSRF_PARAMS:
                    key = (u, k)
                    if key not in seen:
                        seen.add(key)
                        candidates.append(key)
        for k in ("url", "src", "link", "fetch", "proxy"):
            key = (ctx.base_url, k)
            if key not in seen:
                candidates.append(key)

        for url, param in candidates[:15]:
            # 基线：正常参数值响应
            base_r = await http_request("GET", url, timeout=8)
            if base_r.status == 0:
                continue
            base_sig = (base_r.text or "")[:200]
            for cb in _CALLBACK_URLS:
                parsed = urlparse(url)
                new_qs = [(kk, cb if kk == param else vv)
                          for kk, vv in parse_qsl(parsed.query,
                                                  keep_blank_values=True)]
                if not any(kk == param for kk, _ in new_qs):
                    new_qs.append((param, cb))
                probe_url = urlunparse(parsed._replace(query=urlencode(new_qs)))
                r = await http_request("GET", probe_url, timeout=10)
                if r.status == 0:
                    continue
                text = r.text or ""
                hit_kind = None
                for kind, sig in _INTERNAL_SIGS.items():
                    # 响应与基线显著不同且命中内部服务指纹
                    if text[:200] != base_sig and sig.search(text[:8000]):
                        hit_kind = kind
                        break
                if hit_kind:
                    findings.append(SuspectFinding(
                        plugin_id=self.id, vuln_type=self.vuln_type,
                        title=f"SSRF：参数 {param} 可请求内部服务（{hit_kind}）",
                        detail=(f"参数 {param} 注入 {cb} 后，响应内容与基线不同"
                                f"且命中 {hit_kind} 服务指纹，服务端发起"
                                f"了攻击者可控的请求（未校验目标地址）。"),
                        payload=f"{param}={cb}",
                        evidence=f"响应命中 {hit_kind} 指纹: {text[:120]!r}",
                        url=probe_url, param=param,
                        vector=self.default_vector, confidence=0.65,
                    ))
                    break
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        import asyncio
        await asyncio.sleep(0.5)
        r = await http_request("GET", finding.url, timeout=10)
        if r.status and (r.text or "") and "127.0.0.1" in finding.payload:
            finding.verified = True
            finding.verify_evidence = f"复现: 回连响应 {r.status}/{len(r.content)}B"
            finding.confidence = min(0.85, finding.confidence + 0.1)
            return finding
        return None

    @staticmethod
    def _abs(base: str, path: str) -> str:
        from urllib.parse import urljoin
        return urljoin(base, path)
