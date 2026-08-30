"""可配置角色编排引擎：用户用 DAG 描述 agent 编排图，引擎按拓扑并行/串行执行。

用户需求：「可配置角色编排」——前端可视化编排 agent 角色+执行图，
用户自己拖拽组合（如 Attacker×3 并行后接 Reviewer）。

本引擎接收一个 workflow DAG（JSON dict 描述），按依赖关系拓扑执行：
  - 同一层无依赖的节点并行（asyncio.gather）
  - 跨层串行（上层输出作为下层输入）
  - 节点输出可被下游节点消费（通过 outputs 字段引用）

workflow schema 示例：
  {
    "nodes": [
      {"id": "modeler", "role": "modeler"},
      {"id": "sqli1", "role": "specialist", "args": {"vuln_type": "sqli"}},
      {"id": "xss1", "role": "specialist", "args": {"vuln_type": "xss"}},
      {"id": "verifier", "role": "verifier"},
      {"id": "reviewer", "role": "reviewer"}
    ],
    "edges": [
      {"from": "modeler", "to": "sqli1", "field": "model"},
      {"from": "modeler", "to": "xss1", "field": "model"},
      {"from": "sqli1", "to": "verifier", "field": "vulns"},
      {"from": "xss1", "to": "verifier", "field": "vulns"},
      {"from": "verifier", "to": "reviewer", "field": "vulns"}
    ]
  }

支持的 role（与已有 agent 对应）：
  modeler / specialist / attacker / verifier / reviewer /
  site_profiler / attack_tree / master / code_auditor
"""
import asyncio
import json
from typing import Any, Callable

from .agent_message_bus import AgentMessageBus
from .base_agent import BaseAgent
from .llm import LLMClient
from .tool_registry import ToolRegistry


class WorkflowDAG:
    """可配置角色编排引擎：解析 workflow DAG 并按拓扑执行。

    用法（orchestrator 调用）：
        dag = WorkflowDAG(workflow_json, run_id, target, llm, tools, memory, on_event)
        result = await dag.execute()
    """

    def __init__(self, workflow: dict, run_id: str, target: Any,
                 llm: LLMClient, tools: ToolRegistry, memory: Any,
                 on_event: Callable[..., None] | None = None,
                 bus: AgentMessageBus | None = None):
        self.workflow = workflow
        self.run_id = run_id
        self.target = target
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.on_event = on_event
        self.bus = bus

        self.nodes: dict[str, dict] = {n["id"]: n for n in workflow.get("nodes", [])}
        self.edges: list[dict] = workflow.get("edges", [])
        # 反向邻接：to -> [from nodes]
        self.parents: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for e in self.edges:
            self.parents[e["to"]].append(e["from"])

        self.outputs: dict[str, dict] = {}  # node_id -> output dict

    async def execute(self) -> dict:
        """拓扑排序 + 同层并行执行。返回每个节点的输出。"""
        # 拓扑分层
        layers = self._topological_layers()
        for layer_idx, layer in enumerate(layers):
            self._emit_event("workflow", f"执行第 {layer_idx+1} 层: {[n for n in layer]}")
            # 同层并行
            tasks = [self._execute_node(nid) for nid in layer]
            await asyncio.gather(*tasks, return_exceptions=False)
        return {"outputs": self.outputs, "layers": layers}

    async def _execute_node(self, node_id: str) -> None:
        """执行单个节点：实例化对应 agent + 注入上游输出 + run。"""
        node = self.nodes[node_id]
        role = node.get("role", "")
        args = node.get("args", {})

        # 组装输入：把上游输出按 edge.field 注入
        task_input: dict = dict(args)
        for parent_id in self.parents[node_id]:
            parent_out = self.outputs.get(parent_id, {})
            # 找到 from=parent_id to=node_id 的 edge，取 field
            for e in self.edges:
                if e["from"] == parent_id and e["to"] == node_id:
                    field = e.get("field", "")
                    if field and field in parent_out:
                        task_input[field] = parent_out[field]
                    elif "vulns" in parent_out and "vulns" not in task_input:
                        # 默认传递 vulns
                        task_input[field or "vulns"] = parent_out["vulns"]

        # 实例化 agent
        agent = self._instantiate_agent(role, node_id)
        if agent is None:
            self._emit_event("workflow", f"未知 role={role} 跳过 node={node_id}")
            self.outputs[node_id] = {"error": f"unknown role {role}"}
            return

        try:
            out = await agent.run(task_input)
            self.outputs[node_id] = out if isinstance(out, dict) else {"result": out}
            self._emit_event("workflow",
                             f"node={node_id} role={role} 完成: "
                             f"{list(self.outputs[node_id].keys())}")
        except Exception as e:  # noqa: BLE001
            self.outputs[node_id] = {"error": str(e)}
            self._emit_event("workflow",
                             f"node={node_id} role={role} 异常: {e}")

    def _instantiate_agent(self, role: str,
                            node_id: str) -> BaseAgent | None:
        """按 role 实例化对应 agent。"""
        # 通用构造参数
        common = dict(run_id=f"{self.run_id}/{node_id}", target=self.target,
                       llm=self.llm, tools=self.tools, memory=self.memory,
                       on_event=self.on_event)
        try:
            if role == "modeler":
                from ..agents.modeler import ModelerAgent
                return ModelerAgent(**common)
            if role == "site_profiler":
                from ..agents.site_profiler import SiteProfilerAgent
                return SiteProfilerAgent(**common)
            if role == "attack_tree":
                from ..agents.attack_tree import AttackTreeAgent
                return AttackTreeAgent(**common)
            if role == "attacker":
                from ..agents.attacker import AttackerAgent
                return AttackerAgent(**common)
            if role == "verifier":
                from ..agents.verifier import VerifierAgent
                return VerifierAgent(**common)
            if role == "reviewer":
                from ..agents.reviewer import ReviewerAgent
                # reviewer 不接 tools
                return ReviewerAgent(self.run_id, target=self.target,
                                     llm=self.llm, on_event=self.on_event)
            if role == "code_auditor":
                from ..agents.code_auditor import CodeAuditorAgent
                return CodeAuditorAgent(**common)
            if role == "master":
                from ..agents.master import MasterAgent
                return MasterAgent(self.run_id, target=self.target,
                                   llm=self.llm, tools=self.tools,
                                   memory=self.memory, on_event=self.on_event,
                                   bus=self.bus)
            if role == "specialist":
                from ..agents.specialists import SPECIALISTS
                vtype = (common.pop("args", {}) or {}).get("vuln_type", "sqli")
                # node.args 里有 vuln_type，但 common 已不含 args
                # 这里从 node 取
                node = next((n for n in self.workflow.get("nodes", [])
                             if n["id"] == node_id), {})
                vtype = node.get("args", {}).get("vuln_type", "sqli")
                cls = SPECIALISTS.get(vtype, SPECIALISTS["sqli"])
                return cls(**common, bus=self.bus)
        except Exception as e:  # noqa: BLE001
            self._emit_event("workflow", f"实例化 agent {role} 失败: {e}")
        return None

    def _topological_layers(self) -> list[list[str]]:
        """Kahn 算法分层拓扑排序：同层无依赖可并行。"""
        # 入度
        indeg: dict[str, int] = {nid: len(self.parents[nid]) for nid in self.nodes}
        layers: list[list[str]] = []
        remaining = set(self.nodes.keys())
        while remaining:
            # 入度为 0 的节点
            zero = [n for n in remaining if indeg[n] == 0]
            if not zero:
                # 出现环，强制打破
                zero = list(remaining)
            layers.append(zero)
            for n in zero:
                remaining.discard(n)
            # 减少下游入度
            for e in self.edges:
                if e["from"] in zero:
                    indeg[e["to"]] -= 1
        return layers

    def _emit_event(self, agent_role: str, msg: str) -> None:
        if self.on_event:
            try:
                # 使用关键字参数传参，避免回调签名变更导致位置错位。
                # 对齐 Orchestrator.emit 的形参名: run_id, target_id, role, level, content
                self.on_event(
                    run_id=self.run_id,
                    target_id=getattr(self.target, "id", ""),
                    role=agent_role,
                    level="info",
                    content=msg,
                )
            except Exception:  # noqa: BLE001
                pass


# 预置 workflow 模板（前端可拖拽组合，也可直接用预置）
PRESET_WORKFLOWS: dict[str, dict] = {
    "default_multi_agent": {
        "name": "默认多 agent 合作",
        "description": "Master 调度 + 4 个专精并行 + Verifier + Reviewer",
        "workflow": {
            "nodes": [
                {"id": "modeler", "role": "modeler"},
                {"id": "master", "role": "master"},
                {"id": "verifier", "role": "verifier"},
                {"id": "reviewer", "role": "reviewer"},
            ],
            "edges": [
                {"from": "modeler", "to": "master", "field": "model"},
                {"from": "master", "to": "verifier", "field": "vulns"},
                {"from": "verifier", "to": "reviewer", "field": "vulns"},
            ],
        },
    },
    "parallel_specialists": {
        "name": "4 专精并行",
        "description": "Modeler → 4 个专精并行 → 去重 → Reviewer",
        "workflow": {
            "nodes": [
                {"id": "modeler", "role": "modeler"},
                {"id": "sqli", "role": "specialist", "args": {"vuln_type": "sqli"}},
                {"id": "xss", "role": "specialist", "args": {"vuln_type": "xss"}},
                {"id": "ssrf", "role": "specialist", "args": {"vuln_type": "ssrf"}},
                {"id": "logic", "role": "specialist", "args": {"vuln_type": "business_logic"}},
                {"id": "reviewer", "role": "reviewer"},
            ],
            "edges": [
                {"from": "modeler", "to": "sqli", "field": "model"},
                {"from": "modeler", "to": "xss", "field": "model"},
                {"from": "modeler", "to": "ssrf", "field": "model"},
                {"from": "modeler", "to": "logic", "field": "model"},
                {"from": "sqli", "to": "reviewer", "field": "vulns"},
                {"from": "xss", "to": "reviewer", "field": "vulns"},
                {"from": "ssrf", "to": "reviewer", "field": "vulns"},
                {"from": "logic", "to": "reviewer", "field": "vulns"},
            ],
        },
    },
}
