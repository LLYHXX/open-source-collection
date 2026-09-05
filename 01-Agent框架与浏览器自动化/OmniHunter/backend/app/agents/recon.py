"""Recon 侦察 Agent：借鉴 DeerFlow 的 recon 与 AutoHunter 的探活预筛。

调用 httpx 探活指纹 + nmap 端口扫描，召回已知情报，
把指纹/技术栈沉淀进记忆库供后续 Worker 复用。
"""
from typing import Any, Callable
from urllib.parse import urlparse

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


def _host(url: str) -> str:
    try:
        return urlparse(url).hostname or url
    except Exception:  # noqa: BLE001
        return url


class ReconAgent(BaseAgent):
    role = "recon"
    description = "侦察：探活指纹 + 端口扫描 + 情报召回与沉淀。"

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router: Any = None, pruning: Any = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event,
                         router=router, pruning=pruning)

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        self.think(f"侦察目标 {url}")

        httpx_out = await self.tools.aexecute("httpx_probe", {"url": url})
        self.tool_call("httpx_probe", {"url": url}, httpx_out)

        host = getattr(self.target, "host", "") or _host(url)
        nmap_out = await self.tools.aexecute("nmap_scan", {"host": host})
        self.tool_call("nmap_scan", {"host": host}, nmap_out)

        intel = self.memory.summary(url) if self.memory else "无记忆系统"
        self.think(f"已知情报:\n{intel}")

        if self.memory:
            self.memory.store("fingerprint", url, httpx_out,
                              confidence=0.7, source=self.target.id)
            self.memory.store("techstack", url, httpx_out,
                              confidence=0.7, source=self.target.id)

        return {"fingerprint": httpx_out, "ports": nmap_out, "intel": intel}
