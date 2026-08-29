"""IDOR 检测插件 —— 基于 idor_traverse 确定性模块。"""
from __future__ import annotations

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..logic import idor_traverse


class IdorPlugin(DetectorPlugin):
    id = "idor.enumerate"
    vuln_type = "idor"
    name = "IDOR 越权访问"
    description = "ID 参数枚举遍历，对比响应内容差异，确定性判定"
    default_vector = "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        await idor_traverse.run_idor_traverse(ctx, findings)
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        return await idor_traverse.verify_idor_finding(ctx, finding)
