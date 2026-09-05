"""Agent 编排器：借鉴 PraisonAI 五层 stack 与 AutoHunter 流水线。

2026-08-30 命中率 + 省 Token 升级：
  - 建立 LLMRouter（规则/小/大三层）单例：参数提取/指纹匹配/固定变异等体力活走规则层 0 Token
  - 建立 PruningPolicy：攻击动作按成功率+危害排序，连续失败自动剪枝，提升确认率
  - 大小模型分开：small LLM 负责简单语义判断，大模型只做关键决策
  - 所有 Agent 统一注入 router / pruning 引用

流水线:
  Collector 收集 → (Recon → Worker: scan/exploit/verify) → Verifier 独立复现
  → Reviewer 极理性初审 → 入库待人工复审
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select

from ..config import get_settings
from ..models import AgentMessage, AgentRun, Intel, Task, Target, Vuln
from . import state_machine
from .llm import LLMClient
from .llm_router import LLMRouter
from .memory import MemoryStore
from .pruning import PruningPolicy
from .tool_registry import ToolRegistry


class Orchestrator:
    def __init__(self, db, settings=None):
        self.db = db
        self.settings = settings or get_settings()
        self.tools = build_tool_registry(self.settings)
        # === 2026-08-30 新增：大小模型分层 + 路由器 + 剪枝（单例共享）===
        self.big_llm: LLMClient = LLMClient(settings=self.settings)
        self.small_llm: LLMClient = LLMClient.small(settings=self.settings)
        self.router: LLMRouter = LLMRouter(
            self.settings, big_llm=self.big_llm, small_llm=self.small_llm
        )
        # PruningPolicy 对每个 Orchestrator 实例复用（内部按 branch_id 隔离不同目标）
        self.pruning: PruningPolicy = PruningPolicy(
            max_consecutive_failures=3,
            stop_on_high_severity=True,
            stop_on_critical=True,
        )

    def router_stats(self) -> dict:
        """前端展示：规则/小/大 各层调用量与估算省下的 Token。"""
        return self.router.stats_summary()

    def pruning_stats(self) -> dict:
        """前端展示：已剪枝分支、命中高危分支、连续失败计数。"""
        return self.pruning.stats()

    def _llm_for(self, role: str) -> LLMClient:
        """简单角色优先配小模型，关键角色用大模型（兜底都用大模型）。"""
        if role in ("collector", "recon", "site_profiler", "browser"):
            return self.small_llm
        return self.big_llm

    def _agent_kwargs(self, run_id: str, target, role: str) -> dict:
        """统一装配 Agent 构造参数（每次创建 Agent 都调用，确保 router/pruning 注入一致）。"""
        return dict(
            run_id=run_id,
            target=target,
            llm=self._llm_for(role),
            tools=self.tools,
            memory=None,  # memory 由调用方按需注入（不同 pipeline 不一样）
            on_event=self.emit,
            router=self.router,
            pruning=self.pruning,
        )

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

    # ===== 自研引擎流水线（确定性优先，LLM 只做兜底初审）=====
    async def run_engine_pipeline(self, task: Task, url: str,
                                  admin_cookie: str = "",
                                  user_cookie: str = "",
                                  _visited: set | None = None,
                                  depth: int = 0):
        """自研检测引擎流水线：指纹前置 → 确定性插件检测 → 独立复现
        → CVSS 自动定级 → Reviewer 仅做极理性抽检 → 入库。

        引擎输出的都是 verify 复现过的确认漏洞，Reviewer 只按 strict 模式
        校准严重性，不重新测试（对齐方案第四步：Reviewer 改规则审核员）。
        task.mode == "engine" 时 run_task 分流到此；定时任务模板同样生效。
        admin_cookie/user_cookie 提供后启用三身份越权遍历。

        持续挖掘：确认信息泄露后自动提取子目标（目录列表链接/备份文件/
        泄露凭据）递归深挖，深度与总量受配置限制防失控。
        """
        from ..agents.reviewer import ReviewerAgent
        from ..engine import ScanEngine

        extra: dict = {}
        if admin_cookie or user_cookie:
            extra["sessions"] = {
                "admin": {"cookie": admin_cookie},
                "user": {"cookie": user_cookie},
            }

        target = Target(task_id=task.id, url=url)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="engine",
            stage="engine", status="running",
        )
        self.db.add(run)
        self.db.commit()

        try:
            engine = ScanEngine(self.settings)

            async def engine_emit(level: str, content: str):
                self.emit(run.id, target.id, "engine", level, content)

            result = await engine.scan(url, emit=engine_emit, extra=extra)
            findings = result.get("findings", [])

            # 入库：引擎已 verify+CVSS 定级，Reviewer 只抽检校准
            vulns_for_review = [{
                "vuln_type": f.get("vuln_type", ""),
                "severity": f.get("severity", "medium"),
                "title": f.get("title", ""),
                "detail": f.get("detail", ""),
                "payload": f.get("payload", ""),
                "evidence": f.get("evidence", ""),
                "repro": f.get("url", ""),
                "verified": f.get("verified", True),
                "confidence": f.get("confidence", 0.7),
            } for f in findings]

            if vulns_for_review:
                reviewer = ReviewerAgent(
                    run.id, target=target,
                    llm=self.big_llm,
                    on_event=self.emit, strict=self.settings.reviewer_strict,
                    router=self.router, pruning=self.pruning,
                )
                rout = await reviewer.run({"vulns": vulns_for_review})
                reviewed = rout.get("vulns", vulns_for_review)
            else:
                reviewed = []

            for v in reviewed:
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=url,
                    vuln_type=v.get("vuln_type", ""),
                    severity=v.get("severity", "medium"),
                    title=v.get("title", ""), detail=v.get("detail", ""),
                    payload=v.get("payload", ""), evidence=v.get("evidence", ""),
                    repro=v.get("repro", ""), status="ai_reviewed",
                    confidence=v.get("confidence", 0.7),
                ))
            self.db.commit()

            # 持续挖掘：确认信息泄露 → 提取子目标递归深挖（确定性，受深度/总量限制）
            if self.settings.engine_followup_enabled and \
                    depth < self.settings.engine_max_depth:
                await self._engine_followup(task, url, findings,
                                            run.id, _visited, depth)

            run.status = "done"
            run.summary = (f"engine: {result.get('stats', {})}")
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, target.id, "engine", "error",
                      f"engine pipeline 异常: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()

    async def _engine_followup(self, task: Task, url: str,
                               findings: list[dict], run_id: str,
                               _visited: set | None, depth: int) -> None:
        """持续挖掘：从确认的信息泄露漏洞提取子目标与凭据，递归深挖。

        - 目录列表链接 / 备份文件衍生路径 / 显式 URL → 下一轮引擎扫描
        - 泄露凭据 / 内网地址 → Intel 情报库（脱敏）
        防失控：同域过滤 + visited 去重 + followup_max_urls 总量上限。
        """
        from urllib.parse import urlparse

        from ..engine.leak_exploit import extract_followups

        visited = _visited if _visited is not None else {url}
        candidates: list[str] = []
        for f in findings:
            if f.get("vuln_type") != "info_leak":
                continue
            fu = extract_followups(f, url)
            for c in fu.get("creds", []):
                self.db.add(Intel(kind="credential", key=c.get("name", "unknown"),
                                  value=c.get("masked", ""), confidence=0.6,
                                  source=f"leak:{url}"))
            if fu.get("private_ips"):
                self.db.add(Intel(
                    kind="leak", key=urlparse(url).netloc,
                    value=f"内网地址: {', '.join(fu['private_ips'][:10])}",
                    confidence=0.7, source=f"leak:{url}"))
            for u in fu.get("urls", []):
                if u not in visited and len(candidates) < self.settings.followup_max_urls:
                    visited.add(u)
                    candidates.append(u)
            for note in fu.get("notes", [])[:3]:
                self.emit(run_id, "", "engine", "info",
                          f"[持续挖掘] {url}: {note}")
        self.db.commit()
        if not candidates:
            return
        self.emit(run_id, "", "engine", "info",
                  f"[持续挖掘] 从泄露中提取 {len(candidates)} 个子目标，"
                  f"递归扫描（深度 {depth + 1}/{self.settings.engine_max_depth}）")
        for u in candidates:
            try:
                await self.run_engine_pipeline(task, u, _visited=visited,
                                               depth=depth + 1)
            except Exception as e:  # noqa: BLE001 —— 单子目标失败不中断深挖
                self.emit(run_id, "", "engine", "error",
                          f"[持续挖掘] 子目标失败 {u}: {e}")

    # ===== 主流程 =====
    async def run_task(self, task_id: str):
        task = self.db.get(Task, task_id)
        if not task:
            return
        task.status = "collecting"
        self.db.commit()

        # 引擎模式：手工/FOFA 目标全部走自研引擎流水线（定时任务同通道）
        if task.mode == "engine":
            task.status = "running"
            self.db.commit()
            urls = [u.strip() for u in (task.manual_targets or "").splitlines()
                    if u.strip()]
            if not urls and task.source in ("fofa", "both"):
                urls = await self._engine_collect_urls(task)
            for u in urls:
                await self.run_engine_pipeline(task, u)
            task.status = "review"
            self.db.commit()
            return

        targets = await self._collect(task)

        task.status = "running"
        self.db.commit()

        # MVP 串行执行各目标（保证 SQLite 单 session 安全）；
        # 并发可后续用独立 session + asyncio.Semaphore(worker_concurrency) 扩展。
        for target in targets:
            await self._worker_pipeline(task, target)

        task.status = "review"
        self.db.commit()

    async def _engine_collect_urls(self, task: Task) -> list[str]:
        """引擎模式资产平台收集：复用 CollectorAgent._platform_collect，
        纯确定性查询不烧 LLM（nl_intent 模式才会用到）。"""
        from ..agents.collector import CollectorAgent

        run = AgentRun(target_id="", agent_role="collector",
                       stage="collect", status="running")
        self.db.add(run)
        self.db.commit()
        agent = CollectorAgent(run.id, **{
            **self._agent_kwargs(run.id, None, "collector"),
            "settings": self.settings,
        })
        urls: list[str] = []
        try:
            items = await agent._platform_collect(_task_brief(task))
            urls = [i.get("url", "") for i in items if i.get("url")]
            run.status = "done"
            run.summary = f"engine collect: {len(urls)} urls"
        except Exception as e:  # noqa: BLE001
            run.status = "failed"
            run.error = str(e)
            self.emit(run.id, "", "collector", "error",
                      f"engine 资产平台收集失败: {e}")
        finally:
            run.finished_at = datetime.utcnow()
            self.db.commit()
        return urls

    async def _collect(self, task: Task) -> list[Target]:
        from ..agents.collector import CollectorAgent

        run = AgentRun(
            target_id="", agent_role="collector",
            stage="collect", status="running",
        )
        self.db.add(run)
        self.db.commit()

        agent = CollectorAgent(
            **self._agent_kwargs(run.id, None, "collector"),
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

        try:
            # 1) Recon 侦察（简单角色 → 小模型）
            recon = ReconAgent(
                **self._agent_kwargs(run.id, target, "recon"),
                memory=memory,
            )
            recon_out = await recon.run({"vuln_types": task.vuln_types})
            run.stage = state_machine.next_stage(run.stage) or run.stage
            run.step += 1
            self.db.commit()

            # 2) Worker: scan → exploit → verify（攻击型角色 → 大模型 + pruning）
            worker = WorkerAgent(
                **self._agent_kwargs(run.id, target, "worker"),
                memory=memory,
            )
            # 技能包注入：启用包的战术指令追加进 Worker 提示词（失败不阻塞）
            try:
                from .skillpacks import prompt_suffix
                skill_prompts = prompt_suffix(self.db)
            except Exception:  # noqa: BLE001
                skill_prompts = ""
            # 内置知识包注入：探测速查（SQL/RCE/WAF 绕过精炼），失败不阻塞
            try:
                import os
                _kq = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   "knowledge", "payload_quickref.md")
                if os.path.isfile(_kq):
                    with open(_kq, "r", encoding="utf-8") as _f:
                        skill_prompts = (skill_prompts or "") + \
                            "\n\n## 内置攻击知识包（仅对已授权目标使用）\n" + _f.read()
            except Exception:  # noqa: BLE001
                pass
            worker_out = await worker.run({
                "vuln_types": task.vuln_types,
                "recon": recon_out,
                "step_budget": self.settings.worker_step_budget,
                "skill_prompts": skill_prompts,
            })

            # 3) Verifier 独立复现（用大模型做严谨判定）
            for v in worker_out.get("vulns", []):
                verifier = VerifierAgent(
                    **self._agent_kwargs(run.id, target, "verifier"),
                    memory=memory,
                )
                vout = await verifier.run({"vuln": v})
                v["verified"] = vout.get("verified", False)
                v["confidence"] = vout.get("confidence", v.get("confidence", 0.5))

            # 4) Reviewer 极理性 AI 初审
            reviewer = ReviewerAgent(
                run.id, target=target,
                llm=self.big_llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
                router=self.router, pruning=self.pruning,
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
        try:
            agent = BrowserAgent(
                **self._agent_kwargs(run.id, target, "browser"),
                memory=memory,
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
        try:
            # AI1 Modeler 业务建模（命中缓存直接复用，不烧 token；接入 router 规则层 CMS 预筛注入攻击模板）
            modeler = ModelerAgent(
                **self._agent_kwargs(run.id, target, "modeler"),
                memory=memory,
            )
            modeler_out = await modeler.run({})
            model = modeler_out.get("business_model", {})

            # SiteProfiler 单站深挖（router 规则层 0 Token 匹配 CMS + 攻击模板注入 profile）
            profiler = SiteProfilerAgent(
                **self._agent_kwargs(run.id, target, "site_profiler"),
                memory=memory,
            )
            profiler_out = await profiler.run({})
            site_profile = profiler_out if isinstance(profiler_out, dict) else {}

            # AttackTree 生成：若规则层已产出 attack_templates（非空），直接作为骨架，节省 80% prompt
            tree_agent = AttackTreeAgent(
                **self._agent_kwargs(run.id, target, "attack_tree"),
                memory=memory,
            )
            tree_out = await tree_agent.run({
                "site_profile": site_profile,
                "business_model": model,
            })
            attack_tree = tree_out.get("attack_tree", {})

            # AI2 Attacker：接入 router（fixed_mutation 规则层前置）+ pruning（无效尝试剪枝）
            attacker = AttackerAgent(
                **self._agent_kwargs(run.id, target, "attacker"),
                memory=memory,
            )
            attacker_out = await attacker.run({
                "model": model,
                "max_rounds": 3,
                "attack_tree": attack_tree,
            })

            # Verifier 独立复现
            for v in attacker_out.get("vulns", []):
                verifier = VerifierAgent(
                    **self._agent_kwargs(run.id, target, "verifier"),
                    memory=memory,
                )
                vout = await verifier.run({"vuln": v})
                v["verified"] = vout.get("verified", False)
                v["confidence"] = vout.get(
                    "confidence", v.get("confidence", 0.5))

            # Reviewer 极理性 AI 初审
            reviewer = ReviewerAgent(
                run.id, target=target,
                llm=self.big_llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
                router=self.router, pruning=self.pruning,
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
                # 自定义 workflow 由 task.params 传入（Task 当前无 params 列，getattr 兜底为空）
                task_params = getattr(task, "params", None)
                workflow = task_params.get("workflow", {}) if isinstance(task_params, dict) else {}

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


    # ===== 单站协作流水线：权限发现专项 + LLM 攻击 Agent 协同 =====
    async def run_collab_pipeline(self, task: Task, url: str,
                                    admin_cookie: str = "",
                                    user_cookie: str = "",
                                    user2_cookie: str = "",
                                    anon_probe: bool = True,
                                    enable_attacker: bool = True):
        """单站协作流水线：用户需求「单站深挖都有什么权限，让 agent 自动挖掘」。

        流水线：
          SiteProfiler 单站资产收集（命中缓存直接复用不烧 token）
          → Modeler 业务建模（router 规则层 CMS 预筛注入攻击模板）
          → PermissionAgent 权限发现专项（5 类权限检测 + 权限矩阵）
          → Attacker（可选，接入 router/pruning 减少无效尝试）
          → Verifier 独立复现 + Reviewer 极理性初审 → 入库

        与 run_traffic_pipeline 区别：
          - collab 侧重「权限专项」，先跑 PermissionAgent 出权限矩阵；
          - traffic 侧重「业务逻辑」，靠 Modeler + Attacker 多轮变异；
          - 用户可同时跑两条流水线，互补覆盖。
        """
        from ..agents.modeler import ModelerAgent
        from ..agents.site_profiler import SiteProfilerAgent
        from ..agents.permission import PermissionAgent
        from ..agents.verifier import VerifierAgent
        from ..agents.reviewer import ReviewerAgent

        target = Target(task_id=task.id, url=url)
        self.db.add(target)
        self.db.commit()

        run = AgentRun(
            target_id=target.id, agent_role="collab",
            stage="collab", status="running",
        )
        self.db.add(run)
        self.db.commit()

        memory = MemoryStore(self.db)
        # 身份会话（admin/user/user2，由前端提供 Cookie）
        sessions: dict = {}
        if admin_cookie:
            sessions["admin"] = {"cookie": admin_cookie}
        if user_cookie:
            sessions["user"] = {"cookie": user_cookie}
        if user2_cookie:
            sessions["user2"] = {"cookie": user2_cookie}

        all_vulns: list[dict] = []
        try:
            # 1) SiteProfiler 单站深挖自动收集（命中缓存直接复用）
            profiler = SiteProfilerAgent(
                **self._agent_kwargs(run.id, target, "site_profiler"),
                memory=memory,
            )
            profiler_out = await profiler.run({})
            site_profile = profiler_out if isinstance(profiler_out, dict) else {}

            # 2) Modeler 业务建模（router 规则层 0 Token CMS 预筛 + 攻击模板）
            modeler = ModelerAgent(
                **self._agent_kwargs(run.id, target, "modeler"),
                memory=memory,
            )
            modeler_out = await modeler.run({})
            model = modeler_out.get("business_model", {})

            # 3) PermissionAgent 权限发现专项（核心）
            perm_agent = PermissionAgent(
                **self._agent_kwargs(run.id, target, "permission"),
                memory=memory,
            )
            perm_out = await perm_agent.run({
                "url": url,
                "site_profile": site_profile,
                "sessions": sessions,
                "anon_probe": anon_probe,
            })
            perm_vulns = perm_out.get("vulns", [])
            all_vulns.extend(perm_vulns)
            self.emit(run.id, target.id, "permission", "info",
                      f"权限矩阵 {len(perm_out.get('permission_matrix', []))} 行，"
                      f"疑似漏洞 {len(perm_vulns)} 条")

            # 4) Attacker（可选）：基于权限矩阵 + 业务模型做变异攻击
            if enable_attacker and perm_vulns:
                try:
                    from ..agents.attacker import AttackerAgent
                    attacker = AttackerAgent(
                        **self._agent_kwargs(run.id, target, "attacker"),
                        memory=memory,
                    )
                    attacker_out = await attacker.run({
                        "model": model,
                        "max_rounds": 2,
                        "permission_findings": perm_vulns,
                    })
                    all_vulns.extend(attacker_out.get("vulns", []))
                except Exception as e:  # noqa: BLE001 —— Attacker 失败不中断流水线
                    self.emit(run.id, target.id, "attacker", "error",
                              f"Attacker 异常（不中断流水线）: {e}")

            # 5) Verifier 独立复现
            for v in all_vulns:
                verifier = VerifierAgent(
                    **self._agent_kwargs(run.id, target, "verifier"),
                    memory=memory,
                )
                vout = await verifier.run({"vuln": v})
                v["verified"] = vout.get("verified", False)
                v["confidence"] = vout.get(
                    "confidence", v.get("confidence", 0.5))

            # 6) Reviewer 极理性 AI 初审
            reviewer = ReviewerAgent(
                run.id, target=target,
                llm=self.big_llm,
                on_event=self.emit, strict=self.settings.reviewer_strict,
                router=self.router, pruning=self.pruning,
            )
            rout = await reviewer.run({"vulns": all_vulns})

            # 7) 入库待人工复审
            for v in rout.get("vulns", []):
                if v.get("status") == "discard":
                    continue
                self.db.add(Vuln(
                    task_id=task.id, target_id=target.id, target_url=url,
                    vuln_type=v.get("vuln_type", "permission"),
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
            self.emit(run.id, target.id, "collab", "error",
                      f"collab pipeline 异常: {e}")
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
    """装配命令行工具 + 浏览器工具 + MCP 工具（在 tools 模块统一注册）。"""
    from ..tools import register_all

    reg = ToolRegistry()
    register_all(reg, settings)
    # === MCP 注入：启用服务器的全部工具注册进统一注册表（失败不阻塞任务）===
    import logging

    _log = logging.getLogger("aififteen-hunter")
    try:
        from ..database import SessionLocal
        from .mcp_manager import get_mcp_manager

        db = SessionLocal()
        try:
            n = get_mcp_manager().load_into_registry(reg, db)
            if n:
                _log.info("MCP 工具注入完成: %d 个", n)
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        _log.warning("MCP 工具注入失败（不阻塞任务）: %s", e)
    return reg
