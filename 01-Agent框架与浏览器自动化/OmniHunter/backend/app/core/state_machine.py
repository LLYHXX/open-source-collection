"""任务/目标状态机：借鉴 LoopX 的关卡式（stage）推进 + evidence 准入。

关卡序列：recon → scan → exploit → verify → report
每个关卡需有 evidence 才能推进，避免无脑发散。
"""
from __future__ import annotations

STAGES = ["recon", "scan", "exploit", "verify", "report"]

# 关卡准入：推进到下一关需要的 evidence 类型（借鉴 LoopX evidence 准入）
STAGE_GATES: dict[str, str] = {
    "recon": "资产指纹/端口/技术栈",
    "scan": "可疑点/潜在漏洞点",
    "exploit": "可利用 PoC/证据",
    "verify": "独立复现结果",
    "report": "完整报告",
}


def first_stage() -> str:
    return STAGES[0]


def next_stage(current: str | None) -> str | None:
    if not current:
        return STAGES[0]
    if current not in STAGES:
        return STAGES[0]
    idx = STAGES.index(current)
    if idx + 1 >= len(STAGES):
        return None
    return STAGES[idx + 1]


def stage_index(current: str) -> int:
    return STAGES.index(current) if current in STAGES else 0


def gate_requirement(stage: str) -> str:
    return STAGE_GATES.get(stage, "")


def is_terminal(stage: str | None) -> bool:
    return stage == STAGES[-1]
