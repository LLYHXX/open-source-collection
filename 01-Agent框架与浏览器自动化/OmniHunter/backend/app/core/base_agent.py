"""Agent 基类：借鉴 DeerFlow 的 sub-agents 与 Superpowers 的 subagent-driven 模式。

Agent 不直接依赖 DB：通过 on_event 回调上报事件，由 orchestrator 持久化到 AgentMessage，
解耦且便于测试。
"""
from abc import ABC, abstractmethod
from typing import Any, Callable

from .llm import LLMClient
from .tool_registry import ToolRegistry


class BaseAgent(ABC):
    role: str = "base"
    description: str = ""

    def __init__(
        self,
        run_id: str,
        target: Any = None,
        llm: LLMClient | None = None,
        tools: ToolRegistry | None = None,
        memory: Any = None,
        on_event: Callable[..., None] | None = None,
    ):
        self.run_id = run_id
        self.target = target
        self.llm = llm or LLMClient()
        self.tools = tools or ToolRegistry()
        self.memory = memory
        self.on_event = on_event or (lambda **kw: None)

    def emit(self, level: str, content: str, tool: str = "",
             tool_args: dict | None = None, tool_result: str = "") -> None:
        self.on_event(
            run_id=self.run_id,
            target_id=getattr(self.target, "id", "") if self.target else "",
            role=self.role,
            level=level,
            content=content,
            tool=tool,
            tool_args=tool_args or {},
            tool_result=tool_result,
        )

    def think(self, content: str) -> None:
        self.emit("think", content)

    def tool_call(self, name: str, args: dict, result: str) -> None:
        self.emit("tool", f"调用 {name}", tool=name, tool_args=args, tool_result=result)

    def system_prompt(self, context: str = "") -> str:
        base = f"你是 {self.role} Agent。{self.description}".strip()
        return f"{base}\n{context}" if context else base

    def react(self, messages: list[dict], tools: list[dict] | None = None,
              max_steps: int = 8) -> tuple[str, list[dict]]:
        tool_schemas = tools if tools is not None else self.tools.schemas()

        def _executor(name: str, args: dict) -> str:
            return self.tools.execute(name, args)

        return self.llm.react(
            messages,
            tool_schemas,
            _executor,
            max_steps=max_steps,
            on_step=lambda s: self.tool_call(
                s.get("tool", ""), s.get("args", {}), str(s.get("result", ""))
            ),
        )

    @abstractmethod
    def run(self, task_input: dict) -> dict:
        """子类实现：接收输入，返回结构化结果。"""
        ...
