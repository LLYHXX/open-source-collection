"""Agent 基类：借鉴 DeerFlow 的 sub-agents 与 Superpowers 的 subagent-driven 模式。

Agent 不直接依赖 DB：通过 on_event 回调上报事件，由 orchestrator 持久化到 AgentMessage，
解耦且便于测试。

2026-08-30 升级：接入 LLMRouter（规则/小/大三层路由）与 PruningPolicy（攻击剪枝），
把费 Token 的体力活从大模型分流出去，提升命中率 + 省 Token。
"""
from abc import ABC, abstractmethod
from typing import Any, Callable

from .llm import LLMClient
from .tool_registry import ToolRegistry

try:  # 允许不启动路由器时直接导入
    from .llm_router import LLMRouter  # type: ignore
except Exception:  # noqa: BLE001
    LLMRouter = Any  # type: ignore
try:
    from .pruning import PruningPolicy  # type: ignore
except Exception:  # noqa: BLE001
    PruningPolicy = Any  # type: ignore


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
        router: "LLMRouter | None" = None,
        pruning: "PruningPolicy | None" = None,
    ):
        self.run_id = run_id
        self.target = target
        self.llm = llm or LLMClient()
        self.tools = tools or ToolRegistry()
        self.memory = memory
        self.on_event = on_event or (lambda **kw: None)
        # === 2026-08-30 新增：路由器 + 剪枝 ===
        # router 提供 dispatch(task_type, *args, **kwargs) — 规则/小模型分流省 Token
        # pruning 提供 should_execute / record_failure / record_vuln_found — 减少无效尝试提升命中率
        self.router = router
        self.pruning = pruning
        if self.router is None:
            try:
                from .llm_router import LLMRouter as _R
                # 没有显式传入时，构造一个本地路由（兜底不破坏原有 API 兼容）
                self.router = _R(
                    settings=getattr(llm, "settings", None),
                    big_llm=self.llm,
                    small_llm=self.llm,
                )
            except Exception:  # noqa: BLE001
                self.router = None
        if self.pruning is None:
            try:
                from .pruning import PruningPolicy as _P
                self.pruning = _P()
            except Exception:  # noqa: BLE001
                self.pruning = None

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

    async def areact(self, messages: list[dict], tools: list[dict] | None = None,
                     max_steps: int = 8) -> tuple[str, list[dict]]:
        """react 的异步版：整个 ReAct 循环（LLM+工具）在线程池跑，不阻塞事件循环。"""
        tool_schemas = tools if tools is not None else self.tools.schemas()

        def _executor(name: str, args: dict) -> str:
            return self.tools.execute(name, args)

        return await self.llm.areact(
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
