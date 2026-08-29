"""越权检测插件 —— 基于 auth_traverse 三身份确定性模块。"""
from __future__ import annotations

from ..base import DetectorPlugin, ScanContext, SuspectFinding
from ..logic import auth_traverse


class AuthBypassPlugin(DetectorPlugin):
    id = "authbypass.traverse"
    vuln_type = "unauthorized_access"
    name = "水平/垂直越权"
    description = "管理员/普通用户/未登录三身份对比，响应差异超阈值判定越权"
    default_vector = "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N"

    async def detect(self, ctx: ScanContext) -> list[SuspectFinding]:
        findings: list[SuspectFinding] = []
        await auth_traverse.run_auth_traverse(ctx, findings)
        return findings

    async def verify(self, ctx: ScanContext,
                     finding: SuspectFinding) -> SuspectFinding | None:
        return await auth_traverse.verify_auth_finding(ctx, finding)
