"""命令执行检测插件 —— echo marker + 时间盲注（确定性规则）。"""
from __future__ import annotations

import secrets

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request
from ._common import discover_inject_points

# 命令注入 payload 模板（{m} 为 marker）
_CMD_PAYLOADS = (
    ";echo {m}", "|echo {m}", "`echo {m}`", "$(echo {m})",
    ";echo {m};#", "| echo {m}", "&&echo {m}",
    "%0aecho {m}",  # 换行注入（header/mail 场景）
)
# 时间盲注：目标睡眠秒数
_SLEEP_PAIRS = (";sleep {s}", "|sleep {s}", "`sleep {s}`", "$(sleep {s})")


class RcePlugin(DetectorPlugin):
    id = "rce.echo_sleep"
    vuln_type = "rce"
    name = "命令注入（回显/时间盲注）"
    description = "echo marker 回显探测 + sleep 时间差判定，确定性规则"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        points = await discover_inject_points(ctx)
        marker = "cmd" + secrets.token_hex(5)

        for pt in points:
            for param in pt["params"][:6]:
                # --- 回显通道 ---
                for tpl in _CMD_PAYLOADS:
                    payload = tpl.format(m=marker)
                    r = await http_request("GET", pt["url"],
                                           params={param: "1" + payload},
                                           timeout=8)
                    if r.status and marker in (r.text or ""):
                        findings.append(SuspectFinding(
                            plugin_id=self.id, vuln_type=self.vuln_type,
                            title=f"命令注入（回显）：参数 {param}",
                            detail=(f"参数 {param} 值拼接进系统命令执行，"
                                    f"注入 {payload} 后响应回显 marker "
                                    f"({marker})。"),
                            payload=f"{param}=1{payload}",
                            evidence=f"marker {marker} 回显于 {r.status} 响应",
                            url=pt["url"], param=param,
                            vector=self.default_vector, confidence=0.8,
                        ))
                        break

                # --- 时间盲注通道 ---
                base = await http_request("GET", pt["url"],
                                          params={param: "1"}, timeout=15)
                if base.status == 0 or base.elapsed < 0.1:
                    continue
                for tpl in _SLEEP_PAIRS:
                    payload = tpl.format(s=4)
                    r = await http_request("GET", pt["url"],
                                           params={param: "1" + payload},
                                           timeout=15)
                    if r.status and r.elapsed - base.elapsed >= 3.0:
                        findings.append(SuspectFinding(
                            plugin_id=self.id, vuln_type=self.vuln_type,
                            title=f"命令注入（时间盲注）：参数 {param}",
                            detail=(f"参数 {param} 注入 sleep(4) 后响应延迟 "
                                    f"{r.elapsed - base.elapsed:.1f}s"
                                    f"（基线 {base.elapsed:.1f}s），"
                                    f"注入内容进入系统命令执行。"),
                            payload=f"{param}=1{payload}",
                            evidence=(f"base {base.elapsed:.2f}s -> "
                                      f"payload {r.elapsed:.2f}s"),
                            url=pt["url"], param=param,
                            vector=self.default_vector, confidence=0.7,
                        ))
                        break
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        """独立复现：重放 payload，marker/延迟仍复现才确认。"""
        import asyncio
        await asyncio.sleep(0.5)
        if "=" not in finding.payload or not finding.param:
            return None
        value = finding.payload.split("=", 1)[-1]
        r = await http_request("GET", finding.url,
                               params={finding.param: value}, timeout=15)
        if r.status == 0:
            return None
        # 回显型：marker 仍在；时间型：延迟仍 >3s（与 payload 特征比对）
        import re
        m = re.search(r"cmd[0-9a-f]{10}", finding.payload)
        if m and m.group(0) in (r.text or ""):
            finding.verified = True
            finding.verify_evidence = f"复现: marker {m.group(0)} 仍回显"
            finding.confidence = min(0.92, finding.confidence + 0.12)
            return finding
        if "sleep" in value and r.elapsed >= 3.0:
            finding.verified = True
            finding.verify_evidence = f"复现: 延迟 {r.elapsed:.1f}s"
            finding.confidence = min(0.88, finding.confidence + 0.1)
            return finding
        return None
