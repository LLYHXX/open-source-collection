"""工具注册：统一工具调用层，预留 MCP 协议（借鉴 agentmemory MCP + DeerFlow）。

- 命令行工具（nmap/nuclei/sqlmap/httpx）通过适配器注册为可调用工具；
- 后续可挂载 MCP server 工具（register_mcp），统一调度入口不变。
"""
from __future__ import annotations

import json
from typing import Any, Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        fn: Callable[..., Any],
        description: str = "",
        parameters: dict | None = None,
    ) -> None:
        self._tools[name] = {
            "fn": fn,
            "desc": description,
            "params": parameters or {"type": "object", "properties": {}},
        }

    def schemas(self) -> list[dict]:
        """OpenAI function-calling 格式。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": t["desc"],
                    "parameters": t["params"],
                },
            }
            for name, t in self._tools.items()
        ]

    def execute(self, name: str, args: dict | None = None) -> str:
        if name not in self._tools:
            return f"未知工具: {name}"
        try:
            result = self._tools[name]["fn"](**(args or {}))
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False)
            return str(result)
        except Exception as e:  # noqa: BLE001
            return f"工具执行错误[{name}]: {e}"

    async def aexecute(self, name: str, args: dict | None = None) -> str:
        """异步执行：把同步工具丢进线程池，避免阻塞事件循环。

        工具本体（nmap/httpx 子进程、MCP 桥接等）仍是同步实现，
        统一在线程里跑，uvicorn 主循环保持响应。
        """
        return await asyncio.to_thread(self.execute, name, args)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def has(self, name: str) -> bool:
        return name in self._tools
