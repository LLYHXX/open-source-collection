"""Agent 编排器：借鉴 PraisonAI 五层 stack 与 AutoHunter 流水线。

流水线:
  Collector 收集 → (Recon → Worker: scan/exploit/verify) → Verifier 独立复现
  → Reviewer 极理性初审 → 入库待人工复审

事件流持久化到 AgentMessage，供控制台实时看板（AutoHunter 事件流 + DeerFlow trace）。
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select

from ..config import get_settings
from ..models import AgentMessage, AgentRun, Task, Target, Vuln
from . import state_machine
from .llm import LLMClient
from .memory import MemoryStore
from .tool_registry import ToolRegistry


class Orchestrator:
    def __init__(self, db, settings=None):
        self.db = db
        self.settings = settings or get_settings()
        self.tools = build_tool_registry(self.settings)

    # ===== 事件持久化 =====
    def emit(self, run_id, target_id, role, level, content, tool="",
             tool_args=None, tool_result=""):
        msg = AgentMessage(
            run_id=run_id, target_id=target_id, role=role, level=level,
            content=content, tool=tool, tool_args=tool_args or {},
            tool_result=tool_result,
        )
        self.db.add(msg)
        # flush 拿 id 不提交事务，由各 pipeline 关键状态变更点的 commit 一并提交，
        # 避免 SQLite 高频 commit 拖慢事件密集的流水线
        self.db.flush()

    # ===== 主流程 =====
    async def run_task(self, task_id: str):
        task = self.db.get(Task, task_id)
        if not task:
            return
        task.status = "collecting"
        self.db.commit()

        targets = await self._collect(task)

        task.status = "running"
        self.db.commit()

        # MVP 串行执行各目标（保证 SQLite 单 session 安全）；
        # 并发可后续用独立 session + asyncio.Semaphore(worker_concurrency) 扩展。
        for target in targets:
            await self._worker_pipeline(task, target)

        task.status = "review"
        self.db.commit()

    async def _collect(self, task: Task) -> list[Target]:
        from ..agents.collector import CollectorAgent

        run = AgentRun(
            target_id="", agent_role="collector",
            stage="collect", status="running",
        )
        self.db.add(run)
        self.db.commit()

        agent = CollectorAgent(
            run.id, llm=LLMClient(settings=self.settings),
            tools=self.tools, on_event=self.emit,
        )
        result = await agent.run({"task": _task_brief(task)})

        targets: list[Target] = []
        for item in result.get("targets", []):
            url = item if isinstance(item, str) else item.get("url", "")
            if not url:
                continue
            t = Target(
                task_id=task.id, url=url,
                host=item.get("host", "") if isinstance(item, dict) else "",
                title=item.get("title", "") if isinstance(item, dict) else "",
                org=item.get("org", "") if isinstance(item, dict) else "",
            )
            self.db.add(t)
            targets.append(t)
        self.db.commit()

        run.status = "done"
        run.finished_at = datetime.utcnow()
        self.db.commit()
        return targets

    async def _worker_pipeline(self, task: Task, target: Target):
        from ..agents.recon import ReconAgent
        from ..agents.worker import WorkerAgent
        from ..agents.verifier import VerifierAgent
        from ..agents.reviewer import ReviewerAgent

        run = AgentRun(
            target_id=target.id, agent_role="worker",
            stage=state_machine.first_stage(), step=0,
            step_budget=self.settings.worker_step_budget, status="running",
        )
        self.db.add(run)
        self.db.commit()
        target.status = "running"
        self.db.commit()

        memory = MemoryStore(self.db)
        llm = LLMClient(settings=self.settings)

        try:
            # 1) Recon 侦察
            recon = ReconAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            recon_out = await recon.run({"vuln_types": task.vuln_types})
            run.stage = state_machine.next_stage(run.stage) or run.stage
            run.step += 1
            self.db.commit()

            # 2) Worker: scan → exploit → verify 关卡推进
            worker = WorkerAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            worker_out = await worker.run({
                "vuln_types": task.vuln_types,
                "recon": recon_out,
                "step_budget": self.settings.worker_step_budget,
            })

            # 3) Verifier 独立复现（借鉴 Strix / Xalgorix 发现-验证闭环）
            for v in worker_out.get("vulns", []):
                verifier = VerifierAgent(
                    run.id, target=target, llm=llm,
                    tools=self.tools, memory=memory, on_event=self.emit,
                )
                vout = await verifier.run({"vuln": v})
                v["verified"] = vout.get("verified", False)
                v["confidence"] = vout.get("confidence", v.get("confidence", 0.5))

            # 4) Reviewer 极理性 AI 初审
            reviewer = ReviewerAgent(
                run.id, target=target, llm=llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
            )
            rout = await reviewer.run({"vulns": worker_out.get("vulns", [])})

            # 5) 入库待人工复审
            for v in rout.get("vulns", []):
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=target.url,
                    vuln_type=v.get("vuln_type", ""), severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""), evidence=v.get("evidence", ""),
                    repro=v.get("repro", ""), status="ai_reviewed",
                    confidence=v.get("confidence", 0.0),
                ))
            self.db.commit()

            run.status = "done"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, target.id, "worker", "error", f"pipeline 异常: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            target.status = "done"
            self.db.commit()

    # ===== 浏览器单站协作（借鉴 Nanobrowser 多 agent + AutoHunter 单站协作）=====
    async def run_single_site(self, task: Task, url: str):
        from ..agents.browser_agent import BrowserAgent

        target = Target(task_id=task.id, url=url)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="browser",
            stage="browser", status="running",
        )
        self.db.add(run)
        self.db.commit()

        memory = MemoryStore(self.db)
        llm = LLMClient(settings=self.settings)
        try:
            agent = BrowserAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            out = await agent.run({"vuln_types": task.vuln_types})
            for v in out.get("vulns", []):
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=target.url,
                    vuln_type=v.get("vuln_type", ""), severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""), evidence=v.get("evidence", ""),
                    status="ai_reviewed", confidence=v.get("confidence", 0.0),
                ))
            self.db.commit()
            run.status = "done"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()

    # ===== 流量驱动业务逻辑漏洞挖掘（多Agent协同闭环）=====
    async def run_traffic_pipeline(self, task: Task, url: str):
        """流量驱动业务逻辑漏洞挖掘闭环：
        Modeler→SiteProfiler→AttackTree→Attacker(多轮,带经验)→Verifier→Reviewer。

        用户协同设计升级版（在原三 Agent 基础上增强）：
          AI1 Modeler 业务建模（命中 Intel 缓存直接复用，不烧 token）
          新增 SiteProfiler 单站深挖自动收集（subdomain/port/web 入口，
                 命中 site_profile 缓存直接复用，不烧 token）
          新增 AttackTree 自动生成攻击树（基于资产+业务模型，给 Attacker
                 提供结构化攻击路径，不凭空猜）
          AI2 Attacker 抓包变异攻击（多轮自进化，回灌 modeler；
                 每轮 store_experience 沉淀经验，下次同站 recall 复用）
          AI3 Verifier 独立复现 + Reviewer 极理性初审入库。
        核心价值：挖多步操作 + 依赖隐含状态变量的复杂业务逻辑漏洞，
                 且每次攻击经验沉淀进记忆，越用越聪明。
        """
        from ..agents.modeler import ModelerAgent
        from ..agents.site_profiler import SiteProfilerAgent
        from ..agents.attack_tree import AttackTreeAgent
        from ..agents.attacker import AttackerAgent
        from ..agents.verifier import VerifierAgent
        from ..agents.reviewer import ReviewerAgent

        target = Target(task_id=task.id, url=url)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="traffic",
            stage="traffic", status="running",
        )
        self.db.add(run)
        self.db.commit()

        memory = MemoryStore(self.db)
        llm = LLMClient(settings=self.settings)
        try:
            # AI1 Modeler 业务建模（命中缓存直接复用，不烧 token）
            modeler = ModelerAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            modeler_out = await modeler.run({})
            model = modeler_out.get("business_model", {})

            # 新增 SiteProfiler 单站深挖自动收集（命中缓存直接复用）
            profiler = SiteProfilerAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            profiler_out = await profiler.run({})
            site_profile = profiler_out if isinstance(profiler_out, dict) else {}

            # 新增 AttackTree 自动生成攻击树（基于资产+业务模型）
            tree_agent = AttackTreeAgent(
                run.id, target=target, llm=llm, memory=memory,
                on_event=self.emit,
            )
            tree_out = await tree_agent.run({
                "site_profile": site_profile,
                "business_model": model,
            })
            attack_tree = tree_out.get("attack_tree", {})

            # AI2 Attacker 抓包变异攻击（带经验召回 + 每轮沉淀 + 攻击树引导）
            attacker = AttackerAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            attacker_out = await attacker.run({
                "model": model,
                "max_rounds": 3,
                "attack_tree": attack_tree,
            })

            # AI3 Verifier 独立复现每个漏洞
            for v in attacker_out.get("vulns", []):
                verifier = VerifierAgent(
                    run.id, target=target, llm=llm,
                    tools=self.tools, memory=memory, on_event=self.emit,
                )
                vout = await verifier.run({"vuln": v})
                v["verified"] = vout.get("verified", False)
                v["confidence"] = vout.get(
                    "confidence", v.get("confidence", 0.5))

            # AI3 Reviewer 极理性 AI 初审
            reviewer = ReviewerAgent(
                run.id, target=target, llm=llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
            )
            rout = await reviewer.run({"vulns": attacker_out.get("vulns", [])})

            # 入库待人工复审
            for v in rout.get("vulns", []):
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=target.url,
                    vuln_type=v.get("vuln_type", "business_logic"),
                    severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""), evidence=v.get("evidence", ""),
                    repro=v.get("repro", ""), status="ai_reviewed",
                    confidence=v.get("confidence", 0.0),
                ))
            self.db.commit()
            run.status = "done"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, target.id, "traffic", "error",
                      f"traffic pipeline 异常: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()

    # ===== 白盒代码审计流水线（用户要求：黑白盒模式分离）=====
    async def run_whitebox_pipeline(self, task: Task, source_path: str,
                                     severity: str = "low",
                                     business_context: str = ""):
        """白盒模式：拿到源码就能扫，不依赖目标运行。

        流水线: CodeAuditor(Bandit+Dlint+LLM去误报) → Reviewer(severity校准) → 入库。
        黑盒模式走 run_traffic_pipeline / run_task，本流水线只扫静态源码。
        """
        from ..agents.code_auditor import CodeAuditorAgent
        from ..agents.reviewer import ReviewerAgent

        # 白盒模式 target.url 复用为源码路径（前端传 source_path）
        target = Target(task_id=task.id, url=source_path)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="code_auditor",
            stage="whitebox", status="running",
        )
        self.db.add(run)
        self.db.commit()

        memory = MemoryStore(self.db)
        llm = LLMClient(settings=self.settings)
        try:
            # CodeAuditor 静态扫源码 + LLM 去误报
            auditor = CodeAuditorAgent(
                run.id, target=target, llm=llm, tools=self.tools,
                memory=memory, on_event=self.emit,
            )
            audit_out = await auditor.run({
                "source_path": source_path,
                "severity": severity,
                "business_context": business_context,
            })

            # Reviewer 极理性 severity 校准（verified=False 强制降级）
            reviewer = ReviewerAgent(
                run.id, target=target, llm=llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
            )
            rout = await reviewer.run({"vulns": audit_out.get("vulns", [])})

            # 入库待人工复审
            for v in rout.get("vulns", []):
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id,
                    target_url=source_path,
                    vuln_type=v.get("vuln_type", "code_audit"),
                    severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""),
                    evidence=v.get("evidence", ""),
                    repro=f"{v.get('file', '')}:{v.get('line', 0)}",
                    status="ai_reviewed",
                    confidence=v.get("confidence", 0.0),
                ))
            self.db.commit()
            run.status = "done"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, target.id, "code_auditor", "error",
                      f"whitebox pipeline 异常: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()

    # ===== 多 Agent 合作流水线（4 种形态合一：Master+并行+对话+DAG编排）=====
    async def run_multi_agent_pipeline(self, task: Task, url: str,
                                         workflow_name: str = "default_multi_agent"):
        """多 agent 合作流水线：4 种形态合一执行。

        用户需求：Master 调度 + 并行专精 + Agent 间对话 + 可配置 DAG 编排。
        本流水线用 WorkflowDAG 引擎按用户配置的 DAG 拓扑执行，
        节点之间通过 AgentMessageBus 协作对话。

        默认 workflow=default_multi_agent（Master 调度 4 专精+Verifier+Reviewer）。
        前端可传 workflow_name 选择预置，或传自定义 workflow JSON。
        """
        from ..core.agent_message_bus import AgentMessageBus
        from ..core.workflow_dag import PRESET_WORKFLOWS, WorkflowDAG
        from ..agents.modeler import ModelerAgent

        target = Target(task_id=task.id, url=url)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="multi_agent",
            stage="multi_agent", status="running",
        )
        self.db.add(run)
        self.db.commit()

        memory = MemoryStore(self.db)
        llm = LLMClient(settings=self.settings)
        # 每个 run 独立消息总线
        bus = await AgentMessageBus.get_or_create(run.id)

        try:
            # 选 workflow（预置 > 自定义）
            wf_def = PRESET_WORKFLOWS.get(workflow_name, {})
            workflow = wf_def.get("workflow") if wf_def else None
            if workflow is None:
                # 自定义 workflow 由 task.params 传入
                workflow = task.params.get("workflow", {}) if task.params else {}

            if not workflow or not workflow.get("nodes"):
                # 无 workflow 兜底：先跑 Modeler 建 model，
                # 再用 Master 调度（兜底默认 workflow）
                self.emit(run.id, target.id, "multi_agent", "info",
                          f"未配置 workflow，兜底用 default_multi_agent")
                modeler = ModelerAgent(
                    run.id, target=target, llm=llm, tools=self.tools,
                    memory=memory, on_event=self.emit)
                m_out = await modeler.run({})
                model = m_out.get("business_model", {})
                from ..agents.master import MasterAgent
                master = MasterAgent(
                    run.id, target=target, llm=llm, tools=self.tools,
                    memory=memory, on_event=self.emit, bus=bus)
                mout = await master.run({"model": model})
                final_vulns = mout.get("vulns", [])
            else:
                # DAG 引擎执行
                dag = WorkflowDAG(
                    workflow=workflow, run_id=run.id, target=target,
                    llm=llm, tools=self.tools, memory=memory,
                    on_event=self.emit, bus=bus)
                dag_out = await dag.execute()
                # 汇总最后一层（reviewer）的 vulns
                final_vulns = []
                for node_out in dag_out.get("outputs", {}).values():
                    if isinstance(node_out, dict):
                        final_vulns.extend(node_out.get("vulns", []))

            # 入库
            for v in final_vulns:
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=url,
                    vuln_type=v.get("vuln_type", "multi_agent"),
                    severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""),
                    evidence=v.get("evidence", ""),
                    repro=v.get("repro", ""),
                    status="ai_reviewed",
                    confidence=v.get("confidence", 0.0),
                ))
            self.db.commit()
            run.status = "done"
            # 清理消息总线
            AgentMessageBus.drop(run.id)
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, target.id, "multi_agent", "error",
                      f"multi agent pipeline 异常: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()


def _task_brief(task: Task) -> dict:
    return {
        "id": task.id, "name": task.name, "mode": task.mode,
        "source": task.source, "collect_method": task.collect_method,
        "collect_query": task.collect_query, "manual_targets": task.manual_targets,
        "max_pages": task.max_pages, "fofa_override": task.fofa_override,
    }


def build_tool_registry(settings) -> ToolRegistry:
    """装配命令行工具 + 浏览器工具（在 tools 模块统一注册）。"""
    from ..tools import register_all

    reg = ToolRegistry()
    register_all(reg, settings)
    return reg
