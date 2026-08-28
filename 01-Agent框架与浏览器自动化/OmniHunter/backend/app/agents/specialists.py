"""并行专精 Agent：每个 agent 专攻一类漏洞，多 agent 并行挖，结果汇总去重。

用户需求：「并行专精分工」——一个 agent 专挖 SQLi、一个专挖 XSS、
一个专挖业务逻辑、一个专挖 SSRF，并行跑覆盖更全速度更快。

每个 SpecialistAgent 子类化 BaseAgent，构造时带 vuln_type 专精，
run() 用 payload_library + httpx 重放 + LLM 判定，输出本类漏洞清单。
可挂在 AgentMessageBus 上，遇到不懂的字段问 modeler。
"""
import asyncio
import json
from typing import Any, Callable

import httpx

from ..core.agent_message_bus import AgentMessageBus
from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class SpecialistAgent(BaseAgent):
    """专精 agent 基类：子类指定 vuln_type 与 payload category。

    子类只需覆盖 vuln_type / category / description 三个类属性，
    run() 复用基类逻辑：查 payload_library → LLM 选目标端点 → httpx 重放 → 判定。
    """
    vuln_type: str = "generic"
    category: str = ""
    description: str = "专精漏洞挖掘 agent"

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 bus: AgentMessageBus | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)
        self.bus = bus

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        model = task_input.get("model", {})
        api_list = model.get("api_list", [])[:10]

        self.think(f"[{self.vuln_type}] 专精 agent 启动，目标 {url}")

        # 1) 从 payload_library 取本专精的 payload 模板
        payloads_str = self.tools.execute(
            "payload_library",
            {"vuln_type": self.vuln_type, "category": self.category})
        self.tool_call("payload_library",
                        {"vuln_type": self.vuln_type}, payloads_str[:400])

        # 2) LLM 基于业务模型 + payload 模板，选目标端点 + 构造具体攻击请求
        attack_plan = self._plan_attacks(url, model, payloads_str)
        if not attack_plan:
            self.think(f"[{self.vuln_type}] LLM 未生成攻击计划，跳过")
            return {"vulns": [], "vuln_type": self.vuln_type}

        # 3) httpx 异步并发重放
        results = await self._replay_attacks(attack_plan)
        self.think(f"[{self.vuln_type}] 重放 {len(results)} 个攻击请求")

        # 4) LLM 判定哪些响应是真漏洞
        vulns = self._judge_vulns(attack_plan, results, url)
        self.think(f"[{self.vuln_type}] 发现 {len(vulns)} 个候选漏洞")

        # 5) 经验沉淀（按 vuln_type 独立沉淀，下次同类复用）
        if self.memory and vulns:
            site_key = self._site_key(url)
            try:
                self.memory.store_experience(
                    site_key + f":{self.vuln_type}",
                    {"vuln_type": self.vuln_type,
                     "effective_payloads": [{"payload": v.get("payload", "")[:120],
                                              "title": v.get("title", "")}
                                             for v in vulns[:5]],
                     "round_summary": f"{self.vuln_type} 专精发现 {len(vulns)} 个"},
                    confidence=0.7)
            except Exception:  # noqa: BLE001
                pass

        return {"vulns": vulns, "vuln_type": self.vuln_type}

    def _plan_attacks(self, url: str, model: dict, payloads_str: str) -> list[dict]:
        """LLM 选目标端点 + 套 payload 模板生成具体攻击请求清单。"""
        prompt = (
            f"你是 {self.vuln_type} 漏洞专精攻击构造器。基于业务模型与 payload 模板，"
            f"选最可能存在该类漏洞的端点，套用 payload 生成具体攻击请求。\n\n"
            f"目标: {url}\n"
            f"业务模型 api_list: {json.dumps(model.get('api_list', [])[:10], ensure_ascii=False)}\n"
            f"业务规则: {json.dumps(model.get('business_rules', [])[:5], ensure_ascii=False)}\n"
            f"可用 {self.vuln_type} payload 模板:\n{payloads_str[:2000]}\n\n"
            f"输出 JSON 数组（最多 5 条），每项: {{\"method\":\"\",\"url\":\"\","
            f"\"headers\":{{}},\"body\":\"\",\"payload\":\"\",\"intent\":\"\"}}。"
            f"只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, list) else []

    async def _replay_attacks(self, attacks: list[dict]) -> list[dict]:
        """httpx 异步并发重放攻击请求。"""
        try:
            import httpx
        except ImportError:
            return [{"error": "httpx 未安装"} for _ in attacks]

        # nosec B501 — 专精攻击 agent 必须忽略 SSL 校验才能重放到自签/内网站点
        async with httpx.AsyncClient(verify=False, timeout=12,  # nosec B501
                                     follow_redirects=False) as cli:
            tasks = [self._one_attack(cli, a) for a in attacks[:5]]
            return await asyncio.gather(*tasks, return_exceptions=False)

    async def _one_attack(self, cli, attack: dict) -> dict:
        url = attack.get("url", "")
        method = attack.get("method", "GET").upper()
        headers = attack.get("headers", {}) or {}
        body = attack.get("body", "")
        if not url:
            return {"error": "no url"}
        try:
            if method == "GET":
                r = await cli.get(url, headers=headers)
            else:
                r = await cli.request(method, url, headers=headers,
                                      content=body)
            return {"status": r.status_code, "len": len(r.content),
                    "body": r.text[:500], "payload": attack.get("payload", "")}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e), "payload": attack.get("payload", "")}

    def _judge_vulns(self, attacks: list[dict], results: list[dict],
                     url: str) -> list[dict]:
        """LLM 综合判定哪些响应是真漏洞（结合 payload 与响应特征）。"""
        pairs = []
        for i, a in enumerate(attacks):
            r = results[i] if i < len(results) else {}
            pairs.append({
                "payload": a.get("payload", ""),
                "intent": a.get("intent", ""),
                "url": a.get("url", ""),
                "method": a.get("method", ""),
                "status": r.get("status"),
                "body": r.get("body", "")[:300],
            })
        prompt = (
            f"你是 {self.vuln_type} 漏洞判定专家。基于攻击 payload 与响应，"
            f"判定哪些是真实漏洞（区分误报）。\n\n"
            f"目标: {url}\n"
            f"攻击-响应配对:\n{json.dumps(pairs, ensure_ascii=False)}\n\n"
            f"判定规则: 状态码异常 + 响应含敏感数据/报错/反射 = 真漏洞；"
            f"正常 200 + 无异常 = 误报。\n"
            f"输出 JSON 数组（只含真漏洞），每项: {{\"title\":\"\","
            f"\"vuln_type\":\"{self.vuln_type}\",\"severity\":\"low/medium/high\","
            f"\"payload\":\"\",\"target_url\":\"\",\"detail\":\"\",\"evidence\":\"\","
            f"\"confidence\":0-1}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, list) else []

    def _site_key(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
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


# ===== 具体专精 agent（每个一类漏洞）=====
class SQLiSpecialist(SpecialistAgent):
    vuln_type = "sqli"
    category = "union"
    description = "SQL 注入专精：union/boolean/time/error-based 全维度探测"


class XSSSpecialist(SpecialistAgent):
    vuln_type = "xss"
    category = "reflected"
    description = "XSS 专精：reflected/dom/stored 三类探测"


class SSRFSpecialist(SpecialistAgent):
    vuln_type = "ssrf"
    category = "cloud-metadata"
    description = "SSRF 专精：cloud-metadata/internal-port/file 协议探测"


class BusinessLogicSpecialist(SpecialistAgent):
    """业务逻辑漏洞专精：复用 Attacker 的流量驱动思路（轻量版）。

    与 attacker.py 区别：本 agent 是并行专精分工场景下的一员，
    只关注业务逻辑类（IDOR/越权/负价格/跳步骤），不做完整 5 步闭环。
    """
    vuln_type = "business_logic"
    category = ""
    description = "业务逻辑漏洞专精：IDOR/越权/负价格/跳步骤/状态校验位"


# 专精 agent 注册表：name -> class（Master 调度与 workflow_dag 用）
SPECIALISTS: dict[str, type[SpecialistAgent]] = {
    "sqli": SQLiSpecialist,
    "xss": XSSSpecialist,
    "ssrf": SSRFSpecialist,
    "business_logic": BusinessLogicSpecialist,
}
