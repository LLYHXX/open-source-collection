"""Reviewer 复审 Agent：借鉴 AutoHunter 的极理性 AI 初审 + Shannon severity 校准。

只认「实际可利用 + 实锤危害」，过滤半成品 / 误报 / 无危害，
把够格的洞送到人工面前。

Shannon proof-by-exploitation 思想增强：
  - severity 校准：只有 verified=True（Verifier 已反证复现）的漏洞
    才允许标 high/critical；未验证最高 medium，纯理论推测最高 low；
  - 把「无 PoE 证据 + LLM 自评 high」强行降级，避免夸大上报。
"""
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient


class ReviewerAgent(BaseAgent):
    role = "reviewer"
    description = ("极理性 AI 初审 + Shannon severity 校准：只放行实际可利用 + 实锤危害，"
                   "verified=False 强制降级，避免 LLM 夸大上报。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 on_event: Callable[..., None] | None = None,
                 strict: bool = True):
        super().__init__(run_id, target=target, llm=llm, on_event=on_event)
        self.strict = strict

    async def run(self, task_input: dict) -> dict:
        vulns = task_input.get("vulns", [])
        self.think(f"初审 {len(vulns)} 个漏洞，strict={self.strict}")
        prompt = (
            f"你是极理性漏洞初审员。strict={self.strict}。\n"
            f"只保留『实际可利用 + 实锤危害』的漏洞，丢弃半成品/误报/无危害/无证据。\n"
            f"漏洞清单(JSON):\n{json.dumps(vulns, ensure_ascii=False)}\n"
            f"为每个输出裁决 JSON 数组，每项含原字段并加 "
            f"{{\"status\": \"keep\" 或 \"discard\", \"reason\": \"\","
            f" \"severity\": \"critical/high/medium/low/info\"}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, list):
            return {"vulns": vulns}

        # Shannon proof-by-exploitation severity 校准：
        # verified!=True 的漏洞强制降级（最高 medium，纯推测最高 low）
        for item in out:
            if not isinstance(item, dict):
                continue
            item["severity"] = self._calibrate_severity(
                item, verified=bool(item.get("verified", False)))

        return {"vulns": out}

    # ===== Shannon proof-by-exploitation severity 校准 =====
    def _calibrate_severity(self, vuln: dict, verified: bool) -> str:
        """Shannon proof-by-exploitation：未验证漏洞强制降级。

        规则（与用户设计要点一致——只认实锤）：
          - verified=True ：保留 LLM 给的 severity（critical/high/medium/low/info）
          - verified=False：
              * LLM 自评 critical/high → 强制降为 medium
              * LLM 自评 medium → 保留 medium
              * LLM 自评 low/info → 保留
              * 若 confidence < 0.3 或 status=discard → 最高 low
          - 目的：避免未经验证的自评漏洞进入 high/critical 误导人工
        """
        llm_sev = str(vuln.get("severity", "info")).lower().strip()
        confidence = float(vuln.get("confidence", 0.0) or 0.0)
        status = str(vuln.get("status", "keep")).lower()

        # 规范化
        if llm_sev not in ("critical", "high", "medium", "low", "info"):
            llm_sev = "info"

        if verified:
            # 已通过反证复现，保留 LLM 评级
            return llm_sev

        # 未验证：critical/high 强制降 medium
        if llm_sev in ("critical", "high"):
            reason = vuln.get("reason", "")
            vuln["reason"] = (reason +
                              " [Shannon 校准] verified=False，强制 high/critical→medium。")
            return "medium"

        # discard 或低 confidence → 最高 low
        if status == "discard" or confidence < 0.3:
            reason = vuln.get("reason", "")
            vuln["reason"] = (reason +
                              " [Shannon 校准] 未验证且 confidence<0.3 或 discard，最高 low。")
            return "low" if llm_sev in ("medium", "low", "info") else llm_sev

        return llm_sev
