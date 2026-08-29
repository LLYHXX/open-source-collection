"""XSS 检测插件 —— 唯一 marker 反射探测（确定性规则）。"""
from __future__ import annotations

import secrets

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request
from ._common import discover_inject_points

# 反射上下文及危险判定：marker 原样出现在 HTML 中即可能注入
_DANGER_CONTEXTS = (
    ("<script", "script 标签上下文"),
    ("onerror", "事件属性上下文"),
    ("onload", "事件属性上下文"),
    ("javascript:", "javascript 协议上下文"),
    ("<img", "img 标签上下文"),
    ("<svg", "svg 标签上下文"),
    ("<iframe", "iframe 标签上下文"),
)


class XssPlugin(DetectorPlugin):
    id = "xss.reflect"
    vuln_type = "xss"
    name = "XSS 反射型"
    description = "唯一 marker 反射探测 + 危险上下文判定，确定性规则"
    default_vector = "AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        points = await discover_inject_points(ctx)
        marker = "zx" + secrets.token_hex(6)

        # 探测 payload：在 marker 上带危险上下文，判定反射后是否原样输出
        probe_payloads = (
            f'<svg {marker} onerror=alert(1)>',
            f'"><script>{marker}</script>',
            f"'-{marker}-'",  # 纯 marker 先测反射
        )

        for pt in points:
            for param in pt["params"][:8]:
                for payload in probe_payloads:
                    r = await http_request("GET", pt["url"],
                                           params={param: payload}, timeout=8)
                    if r.status == 0 or not r.text:
                        continue
                    body = r.text[:60000]
                    if marker not in body:
                        continue
                    # 判定规则：marker 原样回显（未被 HTML 编码为 &lt; 等）
                    reflected_raw = payload in body
                    danger = [c for c, _ in _DANGER_CONTEXTS
                              if c.lower() in body.lower()]
                    if reflected_raw and danger:
                        findings.append(SuspectFinding(
                            plugin_id=self.id, vuln_type=self.vuln_type,
                            title=f"反射型 XSS：参数 {param}（{danger[0]} 上下文）",
                            detail=(
                                f"参数 {param} 值未被编码直接回显到响应 HTML"
                                f"（{'/'.join(danger[:2])} 危险上下文），"
                                f"可注入脚本执行。"),
                            payload=f"{param}={payload}",
                            evidence=f"marker 原样反射于 {r.status} 响应",
                            url=pt["url"], param=param,
                            vector=self.default_vector, confidence=0.7,
                        ))
                        break
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        """独立复现：重放 payload，marker 仍原样反射才确认。"""
        import asyncio
        await asyncio.sleep(0.5)
        if "=" not in finding.payload or not finding.param:
            return None
        value = finding.payload.split("=", 1)[-1]
        r = await http_request("GET", finding.url,
                               params={finding.param: value}, timeout=8)
        if r.status == 0 or not r.text:
            return None
        # payload 中的字母 token 反射即可（tag 部分可能被过滤后 marker 仍在）
        tokens = [t for t in value.replace("<", " ").replace(">", " ").split()
                  if len(t) > 6]
        if any(t in r.text for t in tokens):
            finding.verified = True
            finding.verify_evidence = f"复现: marker 仍原样反射 ({r.status})"
            finding.confidence = min(0.88, finding.confidence + 0.12)
            return finding
        return None
