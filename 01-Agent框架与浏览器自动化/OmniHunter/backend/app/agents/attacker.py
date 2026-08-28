"""Attacker 攻击探测 Agent（AI2，核心角色）。

闭环核心（用户设计要点逐字保留）：
  ① 基线录制：start_traffic_capture 开启 mitmproxy 监听 + 可选 browser 正常遍历
  ② 隐形参数提取：get_captured_traffic + LLM 分析真实流量，找文档未标注但参与服务端
     逻辑判断的隐形参数（加密 token / cookie 隐含字段 / 状态校验位）
  ③ 参数变异攻击：基于真实请求模板做变异（改ID/负价格/跳步骤/越权换ID），
     用 httpx 重放，而非凭空构造请求
  ④ 异常观测→规则回灌：LLM 观测响应异常生成新规则推测 + 漏洞（business_logic 等）
  ⑤ 回灌 modeler 更新 business_model，开启下一轮迭代 max_rounds

核心价值：挖多步操作 + 依赖隐含状态变量的复杂业务逻辑漏洞（传统扫描器短板）。
"""
import asyncio
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class AttackerAgent(BaseAgent):
    role = "attacker"
    description = ("AI2 攻击探测端（核心）：流量驱动 + 参数变异 + 自进化闭环，"
                   "挖多步业务逻辑漏洞与隐形参数越权。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        model = task_input.get("model", {})
        max_rounds = task_input.get("max_rounds", 3)
        attack_tree = task_input.get("attack_tree", {})

        all_vulns: list[dict] = []
        rules_history: list[dict] = []

        # ===== 经验召回（用户要求：每次攻击都变成经验，下次复用）=====
        site_key = self._site_key(url)
        prior_exp = self._recall_experience(site_key)
        if prior_exp:
            # 把历史经验注入 model.hidden_params_hint，避免重复试错
            hint = model.get("hidden_params_hint", [])
            if not isinstance(hint, list):
                hint = []
            for exp in prior_exp:
                for hp in exp.get("hidden_params", [])[:8]:
                    if isinstance(hp, dict) and hp not in hint:
                        hint.append(hp)
            model["hidden_params_hint"] = hint
            # 把历史有效变异作为本轮起点提示
            self._prior_effective_mutations = [
                m for exp in prior_exp
                for m in exp.get("effective_mutations", [])[:5]
            ]
            self.think(f"召回 {len(prior_exp)} 条历史经验，"
                        f"注入 {len(hint)} 个隐形参数提示 + "
                        f"{len(self._prior_effective_mutations)} 个有效变异模板，"
                        f"避免重复烧 token")
        else:
            self._prior_effective_mutations = []
            self.think("无历史经验，从零开始攻击")

        # 注入攻击树优先动作（让 mutation 不凭空猜）
        self._priority_actions = attack_tree.get("priority_actions", [])

        for round_idx in range(max_rounds):
            self.think(f"=== 迭代第 {round_idx + 1}/{max_rounds} 轮 ===")

            # ① 基线流量录制（开启 mitmproxy 监听 + 等待流量）
            baseline = await self._record_baseline(url, model, round_idx)
            if not baseline:
                # 流量录制失败时回退：用 model.api_list 合成基线请求摘要
                baseline = self._synthesize_baseline_from_model(url, model)
                self.think(f"流量录制失败/无，回退用模型 api_list 合成基线:\n{baseline[:500]}")

            # ② 隐形参数提取（基于真实流量）
            hidden = self._extract_hidden_params(baseline, model, round_idx)
            self.think(f"提取隐形参数: {hidden}")

            # ③ 参数变异 + 重放（基于真实请求模板）
            mutations = self._mutate_requests(baseline, hidden, model, round_idx)
            replay_results = await self._replay_mutations(mutations)
            self.think(f"本轮重放 {len(replay_results)} 个变异请求")

            # ④ 异常观测 → 规则推测 + 漏洞
            new_rules, round_vulns = self._observe_anomalies(
                baseline, replay_results, hidden, model, round_idx)
            all_vulns.extend(round_vulns)
            rules_history.extend(new_rules)

            # ⑤ 经验沉淀（用户要求：每次攻击都变成自己的经验）
            self._store_round_experience(
                site_key, baseline, hidden, mutations, replay_results,
                new_rules, round_vulns, round_idx)

            # ⑥ 回灌 modeler（更新 Intel business_model），开启下一轮
            if new_rules and self.memory:
                self._feedback_to_model(url, model, new_rules)
                self.think(f"回灌 {len(new_rules)} 条新规则到业务模型，开启下一轮")

        # 全部轮次结束，沉淀总结性经验（带最终漏洞清单）
        if self.memory and (all_vulns or rules_history):
            self.memory.store_experience(
                site_key,
                {
                    "hidden_params": self._collect_all_hidden(prior_exp, all_vulns),
                    "effective_mutations": self._collect_effective_mutations(all_vulns),
                    "failed_mutations": self._collect_failed_mutations(rules_history),
                    "discovered_rules": rules_history,
                    "vulns": [{"title": v.get("title", ""),
                               "vuln_type": v.get("vuln_type", ""),
                               "payload": v.get("payload", "")} for v in all_vulns],
                    "round_summary": f"共 {len(all_vulns)} 漏洞，{len(rules_history)} 规则",
                },
                confidence=0.8,
            )
            self.think(f"沉淀总结性经验进记忆 site_key={site_key}")

        return {"vulns": all_vulns, "rules_history": rules_history}

    # ===== 经验沉淀与召回（用户要求：每次攻击都变成经验）=====
    def _site_key(self, url: str) -> str:
        """从 url 提取根域作为经验沉淀 key（同类站共享经验）。"""
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or url
        except Exception:  # noqa: BLE001
            host = url
        host = host.lower().strip()
        for p in ("http://", "https://"):
            if host.startswith(p):
                host = host[len(p):]
        host = host.split("/")[0].split(":")[0]
        parts = host.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else host

    def _recall_experience(self, site_key: str) -> list[dict]:
        """召回该站点历史攻击经验（无 memory 时返回空）。"""
        if not self.memory:
            return []
        try:
            exps = self.memory.recall_experience(site_key, limit=3)
        except Exception:  # noqa: BLE001
            return []
        # 命中复用计数 +1
        for _ in exps:
            self.memory.hit_by_kind_key("attack_experience", site_key)
        return exps

    def _store_round_experience(self, site_key: str, baseline: str,
                                 hidden: dict, mutations: list[dict],
                                 replay_results: list[dict],
                                 new_rules: list[dict], round_vulns: list[dict],
                                 round_idx: int) -> None:
        """每轮结束沉淀本轮经验（失败尝试也记，避免下次重蹈覆辙）。"""
        if not self.memory:
            return
        # 区分有效变异（触发了漏洞/异常）vs 失败变异
        effective: list[dict] = []
        failed: list[dict] = []
        for i, m in enumerate(mutations):
            r = replay_results[i] if i < len(replay_results) else {}
            entry = {
                "mutation_type": m.get("mutation_type", ""),
                "intent": m.get("intent", ""),
                "payload_summary": str(m.get("body", "") or m.get("url", ""))[:120],
                "status": r.get("status") if r else None,
            }
            # 有漏洞产出 或 状态码异常 → effective
            if round_vulns or (r.get("status") and r.get("status") >= 400):
                effective.append(entry)
            else:
                failed.append(entry)

        try:
            self.memory.store_experience(
                site_key,
                {
                    "round_idx": round_idx,
                    "hidden_params": hidden.get("hidden_params", [])[:10],
                    "effective_mutations": effective[:5],
                    "failed_mutations": failed[:5],
                    "discovered_rules": new_rules[:5],
                    "vulns": [{"title": v.get("title", ""),
                               "vuln_type": v.get("vuln_type", "")}
                              for v in round_vulns[:5]],
                    "round_summary": f"第{round_idx+1}轮: "
                                     f"{len(round_vulns)}漏洞/{len(effective)}有效/"
                                     f"{len(failed)}失败",
                },
                confidence=0.65,  # 单轮经验置信度低于总结性
            )
        except Exception:  # noqa: BLE001
            pass

    def _collect_all_hidden(self, prior_exp: list[dict],
                            vulns: list[dict]) -> list[dict]:
        """收集本轮 + 历史所有隐形参数提示（供下次复用）。"""
        all_hidden: list[dict] = []
        for exp in prior_exp:
            for hp in exp.get("hidden_params", []):
                if hp not in all_hidden:
                    all_hidden.append(hp)
        return all_hidden[:20]

    def _collect_effective_mutations(self, vulns: list[dict]) -> list[dict]:
        """从漏洞清单反推有效变异。"""
        out: list[dict] = []
        for v in vulns:
            if v.get("payload"):
                out.append({
                    "vuln_type": v.get("vuln_type", ""),
                    "payload": v.get("payload", "")[:120],
                    "title": v.get("title", ""),
                })
        return out[:10]

    def _collect_failed_mutations(self, rules: list[dict]) -> list[dict]:
        """从规则历史提取失败变异模式（避免下次重试）。"""
        # rules 里 source_evidence 描述了什么变异没触发漏洞
        return [{"rule": r.get("rule", ""),
                 "evidence": r.get("source_evidence", "")}
                for r in rules[:5]]

    # ===== ① 基线录制 =====
    async def _record_baseline(self, url: str, model: dict, round_idx: int) -> str:
        """开启 mitmproxy 监听 + 引导正常业务遍历，录制基线流量。

        实际生产应驱动 browser_agent 正常遍历核心业务流程（登录→下单→支付→退款），
        MVP 阶段留出等待窗口给外部代理或人工触发流量。
        """
        port = 8082 + round_idx
        start = self.tools.execute("start_traffic_capture",
                                   {"proxy_port": port, "duration": 30})
        self.tool_call("start_traffic_capture", {"proxy_port": port}, start)
        if "已开启" not in start:
            return ""
        # 等待基线录制窗口（实际部署应驱动 browser 正常遍历业务流程）
        self.think("等待基线录制中（实际部署应驱动 browser 正常遍历业务流程）")
        await asyncio.sleep(3)
        stop = self.tools.execute("stop_traffic_capture", {})
        self.tool_call("stop_traffic_capture", {}, stop)
        traffic = self.tools.execute("get_captured_traffic", {"max_items": 30})
        self.tool_call("get_captured_traffic", {}, traffic[:1000])
        return traffic

    def _synthesize_baseline_from_model(self, url: str, model: dict) -> str:
        """无流量时回退：用 model.api_list 直接合成基线请求摘要。"""
        api_list = model.get("api_list", [])
        if not api_list:
            return f"目标 {url} 无接口清单。"
        lines = [
            f"{a.get('method', 'GET')} {url.rstrip('/')}/{a.get('path', '').lstrip('/')}"
            for a in api_list[:10]
        ]
        return "\n".join(lines)

    # ===== ② 隐形参数提取 =====
    def _extract_hidden_params(self, baseline: str, model: dict,
                               round_idx: int) -> dict:
        """LLM 从真实流量中提取文档未标注但参与服务端逻辑判断的隐形参数。"""
        hidden_hint = model.get("hidden_params_hint", [])
        prompt = (
            f"你是流量分析专家。从真实抓包流量中提取文档未标注但参与服务端逻辑判断的"
            f"隐形参数（加密 token / cookie 隐含字段 / 状态校验位 / X-CSRF 等）。\n"
            f"基线流量(截断):\n{baseline[:2500]}\n"
            f"模型已提示的隐形参数: {hidden_hint}\n"
            f"输出 JSON: {{\"hidden_params\": [{{\"name\":\"\",\"location\":"
            f"\"header/cookie/body/query\",\"value_pattern\":\"\",\"risk\":\"\"}}]}}。"
            f"只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, dict) else {"hidden_params": []}

    # ===== ③ 参数变异 =====
    def _mutate_requests(self, baseline: str, hidden: dict,
                         model: dict, round_idx: int) -> list[dict]:
        """LLM 基于真实请求模板做参数变异，生成攻击请求清单。"""
        prompt = (
            f"你是业务逻辑漏洞攻击构造器。基于真实基线请求模板做参数变异，"
            f"而非凭空构造请求。\n"
            f"基线流量(截断):\n{baseline[:2500]}\n"
            f"隐形参数: {hidden}\n"
            f"业务规则: {model.get('business_rules', [])}\n"
            f"业务流程: {model.get('flows', [])}\n"
            f"变异方向（择优）：改ID越权 / 负价格 / 跳步骤绕过 / 越权换ID / "
            f"重复提交 / 状态校验位篡改。\n"
            f"输出 JSON 数组，每项: {{\"method\":\"\",\"url\":\"\",\"headers\":{{}},"
            f"\"body\":\"\",\"mutation_type\":\"\",\"intent\":\"\"}}。最多 5 条。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, list) else []

    async def _replay_mutations(self, mutations: list[dict]) -> list[dict]:
        """用 httpx 异步重放变异请求（直接调 httpx 库，不走命令行 httpx_probe）。

        async 版避免阻塞 event loop；变异请求应携带基线 cookie/token 才能测越权，
        LLM 在 _mutate_requests 里已基于真实流量模板填 headers。
        """
        try:
            import httpx
        except ImportError:
            self.think("httpx 库未安装，无法重放变异请求")
            return [{"error": "httpx 未安装"} for _ in mutations]

        results: list[dict] = []
        # nosec B501 — 攻击探测端必须忽略 SSL 校验才能重放变异请求到自签/内网站点
        async with httpx.AsyncClient(verify=False, timeout=15,  # nosec B501
                                     follow_redirects=False) as cli:
            for m in mutations[:5]:
                url = m.get("url", "")
                method = m.get("method", "GET").upper()
                headers = m.get("headers", {}) or {}
                body = m.get("body", "")
                if not url:
                    continue
                try:
                    if method == "GET":
                        r = await cli.get(url, headers=headers)
                    else:
                        r = await cli.request(method, url, headers=headers,
                                              content=body if body else None)
                    results.append({
                        "method": method, "url": url, "status": r.status_code,
                        "body": r.text[:600],
                        "mutation_type": m.get("mutation_type"),
                        "intent": m.get("intent"),
                    })
                    self.tool_call("replay", {"method": method, "url": url},
                                   f"{r.status_code} {r.text[:200]}")
                except Exception as e:  # noqa: BLE001
                    results.append({"method": method, "url": url, "error": str(e)})
        return results

    # ===== ④ 异常观测 → 规则推测 + 漏洞 =====
    def _observe_anomalies(self, baseline: str, replay_results: list[dict],
                           hidden: dict, model: dict,
                           round_idx: int) -> tuple[list[dict], list[dict]]:
        """LLM 观测响应异常 → 规则推测 + 漏洞。"""
        prompt = (
            f"你是业务逻辑漏洞判定器。基于变异重放结果，识别异常并生成"
            f"规则推测与漏洞。\n基线:\n{baseline[:1500]}\n"
            f"变异重放结果:\n{json.dumps(replay_results, ensure_ascii=False)[:3000]}\n"
            f"隐形参数: {hidden}\n业务流程: {model.get('flows', [])}\n"
            f"判定准则：状态码异常/返回越权数据/跳步骤成功/价格负数生效/重复提交幂等失败。\n"
            f"输出 JSON: {{\"new_rules\": [{{\"rule\":\"\",\"source_evidence\":\"\"}}],"
            f" \"vulns\": [{{\"vuln_type\":\"business_logic\","
            f"\"severity\":\"info/low/medium/high/critical\","
            f"\"title\":\"\",\"detail\":\"\",\"payload\":\"\",\"evidence\":\"\","
            f"\"repro\":\"\",\"confidence\":0-1}}]}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            return [], []
        new_rules = out.get("new_rules", [])
        vulns = out.get("vulns", [])
        return (new_rules if isinstance(new_rules, list) else [],
                vulns if isinstance(vulns, list) else [])

    # ===== ⑤ 回灌 modeler =====
    def _feedback_to_model(self, url: str, model: dict,
                           new_rules: list[dict]) -> None:
        """把新规则加入 business_model 并更新 Intel 缓存（开启下一轮迭代）。"""
        rules_field = model.get("business_rules", [])
        if not isinstance(rules_field, list):
            rules_field = []
        for r in new_rules:
            rules_field.append({
                "name": r.get("rule", ""),
                "desc": r.get("source_evidence", ""),
                "source": "attacker_inferred",
            })
        model["business_rules"] = rules_field
        # 更新 Intel 里的 business_model 缓存（kind=business_model，key=url）
        # store 追加新条目；recall 时按 confidence/hits 取最新最高
        self.memory.store("business_model", url,
                          json.dumps(model, ensure_ascii=False),
                          confidence=0.8, source="attacker_round")
