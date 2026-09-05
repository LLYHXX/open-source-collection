"""Worker 挖洞 Agent：借鉴 AutoHunter Worker（LLM 自主侦察）+ LoopX 关卡推进 + Superpowers subagent。

LLM 在 ReAct 循环中自主调用工具（httpx/nmap/nuclei/sqlmap）挖洞，
受 step_budget 约束，最终汇总为结构化漏洞清单。
"""
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class WorkerAgent(BaseAgent):
    role = "worker"
    description = "挖洞：LLM 自主调工具链侦察与利用，关卡推进，产出漏洞。"

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router: Any = None, pruning: Any = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event,
                         router=router, pruning=pruning)

    async def run(self, task_input: dict) -> dict:
        recon = task_input.get("recon", {})
        vuln_types = task_input.get("vuln_types", "")
        budget = task_input.get("step_budget", 40)
        url = self.target.url

        intel = recon.get("intel", "无")
        fingerprint = recon.get("fingerprint", "未知")
        tool_names = ", ".join(self.tools.names()) or "无"
        skill_prompts = str(task_input.get("skill_prompts") or "").strip()

        system = self.system_prompt(
            f"目标: {url}\n指纹: {fingerprint}\n已知情报:\n{intel}\n"
            f"关注漏洞类型: {vuln_types}\n可用工具: {tool_names}\n"
            f"规则：1) 只对已授权目标操作 2) 每步调用一个工具并分析结果 "
            f"3) 发现可利用漏洞时记录 payload 与证据 4) 推进 recon→scan→exploit→verify。"
            + (f"\n{skill_prompts}" if skill_prompts else "")
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "开始侦察与挖洞。"},
        ]
        self.think("进入 LLM 自主挖洞循环")
        final, _ = await self.areact(messages, max_steps=min(budget, 8))

        vulns = await self.llm.achat_json([
            {"role": "system",
             "content": "把挖洞过程汇总为漏洞 JSON 数组，每项含 "
             "vuln_type,severity(info/low/medium/high/critical),title,detail,"
             "payload,evidence,repro,confidence(0-1)。无漏洞返回 []。只输出 JSON。"},
            {"role": "user", "content": final},
        ])
        if not isinstance(vulns, list):
            vulns = []
        self.think(f"汇总得到 {len(vulns)} 个潜在漏洞")
        return {"vulns": vulns}
