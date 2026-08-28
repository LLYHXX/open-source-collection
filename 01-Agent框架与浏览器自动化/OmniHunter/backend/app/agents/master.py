"""Master 调度 Agent：像项目经理，动态拆解任务 + 调度多个 Worker。

用户需求：「Master 调度 Worker」——Master 像项目经理，动态拆解任务，
决定下一步调谁（并行专精 / 串行复查 / 对话协作）。

工作流：
  1) LLM 基于目标资产 + 业务模型，拆解出「需要哪些 Worker 上场」
     （如：sqli + xss + business_logic 三个并行专精）
  2) 并行调度各 SpecialistAgent（asyncio.gather）
  3) 收集结果，LLM 判断「是否需要追加 Worker」（如发现疑似 SQLi，
     追加跑 error-based 补充）
  4) 通过 AgentMessageBus 让 Worker 间可对话协作（如 specialist 问
     modeler 字段含义）
  5) 汇总去重输出最终漏洞清单

与 run_traffic_pipeline 区别：本 Master 走并行专精 + 对话协作，
run_traffic_pipeline 走串行 5 步闭环。两者可互补。
"""
import asyncio
import json
from typing import Any, Callable

from ..core.agent_message_bus import AgentMessageBus
from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry
from .specialists import SPECIALISTS, SpecialistAgent


class MasterAgent(BaseAgent):
    role = "master"
    description = ("Master 调度器：像项目经理拆解任务，动态调度多个专精 Worker "
                   "并行/串行执行，通过消息总线协作，结果汇总去重。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 bus: AgentMessageBus | None = None,
                 max_extra_rounds: int = 1):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)
        self.bus = bus
        self.max_extra_rounds = max_extra_rounds

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        model = task_input.get("model", {})
        all_vulns: list[dict] = []
        executed_specialists: list[str] = []

        # 1) LLM 拆解：选哪些专精 agent 上场
        plan = self._plan_workers(url, model)
        worker_types = plan.get("workers", [])
        self.think(f"Master 拆解：首轮调度 {worker_types}")

        # 2) 首轮并行调度
        round_vulns = await self._dispatch_parallel(worker_types, model, round_idx=0)
        executed_specialists.extend(worker_types)
        all_vulns.extend(round_vulns)

        # 3) 追加轮：LLM 判断是否需要补 Worker（如发现疑似 SQLi 追加 error-based）
        for r_idx in range(self.max_extra_rounds):
            extra = self._decide_extra_workers(round_vulns, executed_specialists)
            if not extra:
                self.think(f"追加第 {r_idx+1} 轮：无需补充 Worker")
                break
            self.think(f"追加第 {r_idx+1} 轮：调度 {extra}")
            extra_vulns = await self._dispatch_parallel(extra, model,
                                                        round_idx=r_idx + 1)
            executed_specialists.extend(extra)
            all_vulns.extend(extra_vulns)
            round_vulns = extra_vulns

        # 4) 去重（同 url + 同 vuln_type + 同 payload 视为重复）
        deduped = self._dedup_vulns(all_vulns)
        self.think(f"Master 汇总：原始 {len(all_vulns)} 条 → 去重后 {len(deduped)} 条")

        # 5) 消息总线历史输出（供前端展示 agent 间对话）
        bus_history: list[dict] = []
        if self.bus:
            try:
                bus_history = await self.bus.history()
            except Exception:  # noqa: BLE001
                bus_history = []

        return {"vulns": deduped, "executed_specialists": executed_specialists,
                "bus_history": bus_history}

    def _plan_workers(self, url: str, model: dict) -> dict:
        """LLM 基于目标 + 业务模型选首轮上场的专精 agent。"""
        available = list(SPECIALISTS.keys())
        prompt = (
            f"你是 Master 调度器。基于目标资产与业务模型，选首轮上场的专精 Worker。\n\n"
            f"目标: {url}\n"
            f"业务模型 api_list: {json.dumps(model.get('api_list', [])[:8], ensure_ascii=False)}\n"
            f"业务规则: {json.dumps(model.get('business_rules', [])[:5], ensure_ascii=False)}\n"
            f"可用专精 Worker: {available}\n"
            f"  - sqli: SQL 注入（有数据库交互的端点优先）\n"
            f"  - xss: XSS（有输入回显的端点优先）\n"
            f"  - ssrf: SSRF（有 URL 参数/回调的端点优先）\n"
            f"  - business_logic: 业务逻辑（订单/支付/越权/IDOR）\n\n"
            f"输出 JSON: {{\"workers\": [\"sqli\",\"xss\"],"
            f"\"reason\": \"选择依据\"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            # 默认全上（保守覆盖）
            return {"workers": available, "reason": "默认全上保守覆盖"}
        workers = out.get("workers", [])
        # 过滤掉不存在的
        workers = [w for w in workers if w in SPECIALISTS]
        if not workers:
            workers = available
        return {"workers": workers, "reason": out.get("reason", "")}

    async def _dispatch_parallel(self, worker_types: list[str],
                                  model: dict, round_idx: int) -> list[dict]:
        """并行调度多个专精 agent，收集漏洞。"""
        if not worker_types:
            return []
        tasks = []
        for wtype in worker_types:
            cls = SPECIALISTS.get(wtype)
            if cls is None:
                continue
            worker = cls(self.run_id, target=self.target, llm=self.llm,
                         tools=self.tools, memory=self.memory,
                         on_event=self.on_event, bus=self.bus)
            tasks.append(worker.run({"model": model}))
        if not tasks:
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_vulns: list[dict] = []
        for r in results:
            if isinstance(r, Exception):
                self.think(f"Worker 异常: {r}")
                continue
            if isinstance(r, dict):
                all_vulns.extend(r.get("vulns", []))
        return all_vulns

    def _decide_extra_workers(self, last_vulns: list[dict],
                               executed: list[str]) -> list[str]:
        """LLM 基于上一轮结果判断是否补 Worker。"""
        if not last_vulns:
            return []
        # 已有 vuln_type 集合
        found_types = {v.get("vuln_type", "") for v in last_vulns}
        prompt = (
            f"你是 Master。上一轮发现以下漏洞，判断是否追加 Worker 补打。\n\n"
            f"已执行的 Worker: {executed}\n"
            f"本轮发现 vuln_type: {list(found_types)}\n"
            f"漏洞清单(简): {json.dumps([{'v': v.get('vuln_type'), 't': v.get('title')} for v in last_vulns[:8]], ensure_ascii=False)}\n"
            f"可用专精: {list(SPECIALISTS.keys())}\n\n"
            f"判定: 已执行过的不再调；发现疑似但未确认的 vuln_type 可追加。\n"
            f"输出 JSON: {{\"extra\": [\"sqli\"],\"reason\":\"\"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            return []
        extra = out.get("extra", [])
        # 过滤已执行 + 不存在
        return [w for w in extra if w in SPECIALISTS and w not in executed]

    def _dedup_vulns(self, vulns: list[dict]) -> list[dict]:
        """去重：同 url + vuln_type + payload 视为重复，保留 confidence 高的。"""
        seen: dict[str, dict] = {}
        for v in vulns:
            key = f"{v.get('target_url','')}|{v.get('vuln_type','')}|{v.get('payload','')[:80]}"
            if key not in seen:
                seen[key] = v
            else:
                # 保留 confidence 高的
                if (v.get("confidence", 0)
                        > seen[key].get("confidence", 0)):
                    seen[key] = v
        return list(seen.values())
