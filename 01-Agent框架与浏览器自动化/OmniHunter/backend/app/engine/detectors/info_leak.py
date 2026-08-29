"""敏感信息泄露检测插件 —— .git/.env/备份/调试端点等（确定性规则）。"""
from __future__ import annotations

import re

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..http_client import get
from urllib.parse import urlparse

# (路径, 判定正则, 漏洞标题, CVSS 向量)
_LEAK_TARGETS = (
    ("/.git/HEAD", re.compile(r"ref:\s*refs/"), "Git 仓库泄露（.git 可访问）",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    ("/.env", re.compile(r"(APP_KEY|DB_PASSWORD|AWS_.*KEY|SECRET)", re.I),
     "环境变量文件泄露（.env）",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"),
    ("/.svn/entries", re.compile(r"^\d+|dir", re.M), "SVN 仓库泄露",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"),
    ("/backup.zip", re.compile(r"^PK\x03\x04"), "备份文件泄露（backup.zip）",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    ("/database.sql", re.compile(r"(CREATE TABLE|INSERT INTO)", re.I),
     "数据库导出文件泄露", "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    ("/phpinfo.php", re.compile(r"phpinfo\(\)|PHP Version", re.I),
     "phpinfo 调试页泄露", "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"),
    ("/actuator/env", re.compile(r"(\{.*\}|propertySources|active)", re.I),
     "Spring Boot Actuator 环境信息泄露",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    ("/actuator/heapdump", None, "Spring Boot HeapDump 泄露",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
    ("/swagger.json", re.compile(r"(swagger|openapi)", re.I),
     "Swagger/OpenAPI 文档泄露", "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"),
    ("/debug/vars", re.compile(r"(cmdline|memstats|goroutine)", re.I),
     "Go pprof/debug 调试端点泄露", "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"),
    ("/.DS_Store", re.compile(r"^\x00\x00\x00\x01Bud1"), ".DS_Store 目录列表泄露",
     "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"),
)


class InfoLeakPlugin(DetectorPlugin):
    id = "infoleak.sensitive_files"
    vuln_type = "info_leak"
    name = "敏感信息泄露"
    description = "探测 .git/.env/备份文件/调试端点等敏感信息暴露"
    default_vector = "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        parsed = urlparse(ctx.base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"

        for path, sig, title, vector in _LEAK_TARGETS:
            url = root + path
            r = await get(url, timeout=8, allow_redirects=False)
            if r.status != 200 or not r.content:
                continue
            body = r.content[:256 * 1024]
            text = body.decode("utf-8", "ignore")
            hit = True if sig is None else bool(sig.search(text))
            # heapdump 这类二进制：内容非 HTML 且体积可观也算命中
            if sig is None and path.endswith("heapdump"):
                hit = len(body) > 10000 and b"<html" not in body[:1024].lower()
            if not hit:
                continue
            findings.append(SuspectFinding(
                plugin_id=self.id, vuln_type=self.vuln_type,
                title=title,
                detail=(f"{path} 可被未授权访问（HTTP 200），"
                        f"内容命中敏感特征，可能暴露源码/配置/密钥/内存数据。"),
                payload=f"GET {path}",
                evidence=(sig.search(text).group(0)
                          if sig and sig.search(text) else f"{len(body)}B 二进制内容"),
                url=url, vector=vector, confidence=0.75,
            ))
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        import asyncio
        await asyncio.sleep(0.5)
        r = await get(finding.url, timeout=8, allow_redirects=False)
        if r.status == 200 and r.content:
            finding.verified = True
            finding.verify_evidence = f"复现: {finding.url} 仍 200/{len(r.content)}B"
            finding.confidence = min(0.9, finding.confidence + 0.12)
            return finding
        return None
