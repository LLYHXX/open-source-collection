"""规划器：借鉴 Superpowers 的 spec→plan 与 LoopX 的关卡推进。

为每个关卡生成具体动作清单，evidence 驱动推进，避免无脑发散。
"""
from __future__ import annotations

from . import state_machine
from .llm import LLMClient


class Planner:
    def __init__(self, llm: LLMClient, memory=None):
        self.llm = llm
        self.memory = memory

    def plan_stage(
        self,
        stage: str,
        target,
        vuln_types: str,
        intel_summary: str = "",
    ) -> list[dict]:
        """生成某关卡的具体动作清单。"""
        target_url = getattr(target, "url", str(target))
        prompt = (
            f"你是漏洞挖掘规划器。当前关卡: {stage}\n"
            f"关卡目标: {state_machine.gate_requirement(stage)}\n"
            f"目标: {target_url}\n"
            f"关注漏洞类型: {vuln_types}\n"
            f"已知情报:\n{intel_summary}\n"
            f"请为该关卡产出 3-6 个具体动作，输出纯 JSON 数组，"
            f"每项 {{\"action\": \"动作描述\", \"tool\": \"工具名或无\", \"expected\": \"预期产出\"}}。"
        )
        result = self.llm.chat_json(
            [
                {"role": "system", "content": "你只输出 JSON 数组，无多余文字。"},
                {"role": "user", "content": prompt},
            ]
        )
        if isinstance(result, list):
            return result
        return []
