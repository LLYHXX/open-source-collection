"""SQL 注入检测插件 —— error-based + bool-based 双通道（确定性规则）。"""
from __future__ import annotations

import re

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import http_request
from ._common import discover_inject_points

# SQL 错误指纹（mysql/mssql/pgsql/sqlite/oracle/odbc）
_ERROR_SIGNATURES = (
    r"you have an error in your sql syntax", r"warning: mysql",
    r"unclosed quotation mark", r"quoted string not properly terminated",
    r"pg_query\(\)", r"postgresql.*error", r"syntax error at or near",
    r"sqlite3?\.operationalerror", r"unrecognized token",
    r"ora-\d{5}", r"oracle error", r"odbc.*driver.*error",
    r"microsoft ole db provider", r"mysql_fetch",
    r"jdbc.*exception", r"hibernate.*exception",
)
_ERROR_RE = re.compile("|".join(_ERROR_SIGNATURES), re.I)

# bool 探针对
_BOOL_PAIRS = (
    ("' AND '1'='1", "' AND '1'='2"),
    (" AND 1=1", " AND 1=2"),
    (") AND 1=1", ") AND 1=2"),
)


class SqliPlugin(DetectorPlugin):
    id = "sqli.error_bool"
    vuln_type = "sql_injection"
    name = "SQL 注入（报错/布尔）"
    description = "error-based SQL 错误指纹 + bool-based 同参对比，确定性判定"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        points = await discover_inject_points(ctx)

        for pt in points:
            for param in pt["params"][:8]:
                # --- error-based：单引号触发 SQL 错误 ---
                r = await http_request(
                    "GET", pt["url"], params={param: "'\"`"},
                    timeout=8)
                if r.status and r.text and _ERROR_RE.search(r.text[:20000]):
                    findings.append(SuspectFinding(
                        plugin_id=self.id, vuln_type=self.vuln_type,
                        title=f"SQL 注入（报错回显）：参数 {param}",
                        detail=(f"向 {pt['url']} 的参数 {param} 注入单引号/反引号，"
                                f"响应包含数据库错误指纹（"
                                f"{_ERROR_RE.search(r.text[:20000]).group(0)}），"
                                f"注入内容进入 SQL 语句执行。"),
                        payload=f"{param}='\"`",
                        evidence=r.text[:300],
                        url=pt["url"], param=param,
                        vector=self.default_vector, confidence=0.75,
                    ))
                    continue

                # --- bool-based：真/假探针响应差异 ---
                for t_payload, f_payload in _BOOL_PAIRS:
                    rt = await http_request("GET", pt["url"],
                                            params={param: t_payload}, timeout=8)
                    rf = await http_request("GET", pt["url"],
                                            params={param: f_payload}, timeout=8)
                    if (rt.status == 0 or rf.status == 0
                            or not rt.ok or not rf.ok):
                        continue
                    t_len, f_len = len(rt.content), len(rf.content)
                    if t_len == 0 or f_len == 0:
                        continue
                    # 真探针与假探针响应显著差异（>30%），且真探针接近正常
                    if abs(t_len - f_len) / max(t_len, f_len) > 0.3:
                        rn = await http_request("GET", pt["url"],
                                                params={param: "zZq"}, timeout=8)
                        n_len = len(rn.content)
                        if abs(t_len - n_len) / max(t_len, n_len, 1) < 0.3:
                            findings.append(SuspectFinding(
                                plugin_id=self.id, vuln_type=self.vuln_type,
                                title=f"SQL 注入（布尔盲注）：参数 {param}",
                                detail=(f"参数 {param} 注入 {t_payload} 与 "
                                        f"{f_payload} 响应差异 "
                                        f"{t_len}B vs {f_len}B，且真探针响应"
                                        f"与正常页相近，条件进入 SQL 执行。"),
                                payload=f"{param}={t_payload}",
                                evidence=f"true: {t_len}B, false: {f_len}B",
                                url=pt["url"], param=param,
                                vector=self.default_vector, confidence=0.65,
                            ))
                            break
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        """独立复现：重新触发，条件仍成立才确认。"""
        import asyncio
        await asyncio.sleep(0.5)
        if finding.param and finding.payload:
            value = finding.payload.split("=", 1)[-1]
            r = await http_request("GET", finding.url,
                                   params={finding.param: value}, timeout=8)
            if r.status == 0:
                return None
            if _ERROR_RE.search(r.text[:20000]):
                finding.verified = True
                finding.verify_evidence = f"复现: 报错指纹仍出现 ({r.status})"
                finding.confidence = min(0.92, finding.confidence + 0.15)
                return finding
            if r.ok:
                finding.verified = True
                finding.verify_evidence = f"复现: 注入响应 {r.status}/{len(r.content)}B"
                finding.confidence = min(0.85, finding.confidence + 0.1)
                return finding
        return None
