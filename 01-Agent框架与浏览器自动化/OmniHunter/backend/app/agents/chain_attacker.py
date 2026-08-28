"""Chain Attacker 业务链路状态机 Agent（深层逻辑漏洞专用）。

用户痛点：单请求变异挖不到深层逻辑漏洞（如"加购→确认→支付"链路）。
当第二步请求修改 ID 后，第三步的 token 会失效，无法检测深层漏洞。
必须有状态保持与链路联动设计。

核心方法（用户设计要点）：
  1) 链路识别：用 mitmproxy flow 标记，按时序拼成业务流图，
     识别关键节点（创建→提交→审核→完成）
  2) 三类核心链路变异：
     a) 身份错位：前半段用 A 的 token，后半段用 B 的 token（测水平越权）
     b) 跳步执行：跳过中间 1-2 步，直接调用最终节点接口（测步骤绕过）
     c) 状态回退：对已完成流程，重新调用驳回/取消接口（测状态回滚）

与 attacker.py 区别：
  - attacker.py 是单请求变异 + 多轮回灌闭环
  - 本 agent 专注多步链路级变异，是 attacker 的纵深补充
  - 两者可串联：attacker 跑完单点变异，再调 chain_attacker 挖链路深层
"""
import asyncio
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class ChainAttackerAgent(BaseAgent):
    role = "chain_attacker"
    description = ("业务链路状态机：多步业务流变异（身份错位/跳步/状态回退），"
                   "挖单请求变异挖不到的深层逻辑漏洞。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        model = task_input.get("model", {})
        baseline = task_input.get("baseline", "")

        self.think(f"业务链路变异攻击: url={url}")

        # 1) 链路识别：从基线流量中提取业务流图
        chain = self._identify_chain(baseline, model, url)
        if not chain.get("nodes"):
            self.think("未识别到多步业务链路，跳过链路变异")
            return {"vulns": [], "chain": chain}

        self.think(f"识别链路 {len(chain['nodes'])} 节点: "
                   f"{[n.get('step','') for n in chain['nodes']]}")

        # 2) 三类链路变异
        all_vulns: list[dict] = []

        # a) 身份错位：前段 A token + 后段 B token
        identity_vulns = await self._attack_identity_swap(chain, url)
        all_vulns.extend(identity_vulns)
        self.think(f"身份错位变异: 发现 {len(identity_vulns)} 个候选")

        # b) 跳步执行：跳过中间节点直接调最终接口
        skip_vulns = await self._attack_step_skip(chain, url)
        all_vulns.extend(skip_vulns)
        self.think(f"跳步变异: 发现 {len(skip_vulns)} 个候选")

        # c) 状态回退：对已完成流程调驳回/取消接口
        rollback_vulns = await self._attack_state_rollback(chain, url)
        all_vulns.extend(rollback_vulns)
        self.think(f"状态回退变异: 发现 {len(rollback_vulns)} 个候选")

        # 3) 沉淀经验
        if self.memory and all_vulns:
            site_key = self._site_key(url)
            try:
                self.memory.store_experience(
                    site_key + ":chain",
                    {"chain_vulns": [{"title": v.get("title", ""),
                                       "attack_type": v.get("attack_type", "")}
                                      for v in all_vulns[:5]],
                     "chain_summary": f"链路 {len(chain['nodes'])} 节点，"
                                      f"{len(all_vulns)} 漏洞"},
                    confidence=0.75)
            except Exception:  # noqa: BLE001
                pass

        return {"vulns": all_vulns, "chain": chain}

    def _identify_chain(self, baseline: str, model: dict, url: str) -> dict:
        """LLM 从基线流量中识别多步业务链路（业务流图）。"""
        flows = model.get("flows", [])[:5]
        prompt = (
            f"你是业务链路识别专家。从基线流量中按时序拼出业务流图，"
            f"识别关键节点（如：创建→提交→审核→完成）。\n\n"
            f"目标: {url}\n"
            f"业务流程(模型): {json.dumps(flows, ensure_ascii=False)}\n"
            f"基线流量(截断):\n{baseline[:2500]}\n\n"
            f"输出 JSON: {{\n"
            f"  \"chain_name\": \"业务流名称（如：订单创建到支付）\",\n"
            f"  \"nodes\": [\n"
            f"    {{\n"
            f"      \"step\": 1,\n"
            f"      \"name\": \"节点名（如：加购）\",\n"
            f"      \"method\": \"POST\",\n"
            f"      \"url\": \"\",\n"
            f"      \"key_params\": [\"user_id\",\"order_id\"],\n"
            f"      \"produces\": [\"order_id\"],  # 本步产生的状态变量\n"
            f"      \"consumes\": [\"token\"],     # 依赖的上游变量\n"
            f"      \"auth_required\": true\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"final_node_index\": 3  # 最终状态节点序号（跳步攻击用）\n"
            f"}}。最多 6 节点。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            return {"chain_name": "", "nodes": []}
        out.setdefault("nodes", [])
        out.setdefault("final_node_index", len(out["nodes"]) - 1)
        if not isinstance(out["nodes"], list):
            out["nodes"] = []
        return out

    async def _attack_identity_swap(self, chain: dict, url: str) -> list[dict]:
        """身份错位：前段 A token + 后段 B token（测水平越权）。"""
        nodes = chain.get("nodes", [])
        if len(nodes) < 2:
            return []

        # 找中段节点（既非首也非末）
        mid_idx = len(nodes) // 2
        prompt = (
            f"你是链路越权攻击构造器。身份错位变异："
            f"前 {mid_idx} 步用用户 A 的 token/Cookie 提交，"
            f"后段用用户 B 的 token 操作 B 的资源，测水平越权。\n\n"
            f"链路: {json.dumps(chain, ensure_ascii=False)}\n"
            f"目标: {url}\n\n"
            f"输出 JSON 数组（最多 3 条），每项: {{\n"
            f"  \"attack_type\": \"identity_swap\",\n"
            f"  \"split_step\": {mid_idx},\n"
            f"  \"steps\": [\n"
            f"    {{\"step\": 1, \"use_token\": \"A\", \"url\": \"\", \"method\": \"\","
            f" \"body\": \"\"}},\n"
            f"    {{\"step\": {mid_idx+1}, \"use_token\": \"B\", \"url\": \"\","
            f" \"method\": \"\", \"body\": \"\"}}\n"
            f"  ],\n"
            f"  \"success_signal\": \"如何判定越权成功\"\n"
            f"}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, list):
            return []
        return await self._replay_chain_attacks(out, url)

    async def _attack_step_skip(self, chain: dict, url: str) -> list[dict]:
        """跳步执行：跳过中间节点直接调最终接口（测步骤绕过）。"""
        nodes = chain.get("nodes", [])
        final_idx = chain.get("final_node_index", len(nodes) - 1)
        if final_idx < 2:
            return []

        prompt = (
            f"你是步骤绕过攻击构造器。跳过中间节点，直接调用最终节点接口，"
            f"测服务端是否校验前置步骤完成状态。\n\n"
            f"链路: {json.dumps(chain, ensure_ascii=False)}\n"
            f"最终节点序号: {final_idx}\n"
            f"目标: {url}\n\n"
            f"输出 JSON 数组（最多 3 条），每项: {{\n"
            f"  \"attack_type\": \"step_skip\",\n"
            f"  \"skipped_steps\": [2,3],\n"
            f"  \"target_node\": {final_idx},\n"
            f"  \"method\": \"\",\n"
            f"  \"url\": \"\",\n"
            f"  \"body\": \"\",\n"
            f"  \"success_signal\": \"如何判定绕过成功\"\n"
            f"}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, list):
            return []
        return await self._replay_chain_attacks(out, url)

    async def _attack_state_rollback(self, chain: dict, url: str) -> list[dict]:
        """状态回退：对已完成流程重新调驳回/取消接口（测状态回滚）。"""
        nodes = chain.get("nodes", [])
        if not nodes:
            return []

        prompt = (
            f"你是状态回退攻击构造器。对已完成的业务流程，"
            f"重新调用驳回/取消/退款接口，测试能否回滚已生效数据。\n\n"
            f"链路: {json.dumps(chain, ensure_ascii=False)}\n"
            f"目标: {url}\n\n"
            f"输出 JSON 数组（最多 3 条），每项: {{\n"
            f"  \"attack_type\": \"state_rollback\",\n"
            f"  \"prerequisite\": \"先完成完整流程拿到已完成态\",\n"
            f"  \"method\": \"\",\n"
            f"  \"url\": \"\",\n"
            f"  \"body\": \"\",\n"
            f"  \"success_signal\": \"如何判定回退成功（如状态恢复/退款到账）\"\n"
            f"}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, list):
            return []
        return await self._replay_chain_attacks(out, url)

    async def _replay_chain_attacks(self, attacks: list[dict],
                                      url: str) -> list[dict]:
        """httpx 重放链路攻击请求 + LLM 判定。"""
        try:
            import httpx
        except ImportError:
            return [{"error": "httpx 未安装"}]

        # nosec B501 — 链路攻击需重放到自签/内网站点
        async with httpx.AsyncClient(verify=False, timeout=15,  # nosec B501
                                     follow_redirects=False) as cli:
            results = []
            for a in attacks[:5]:
                method = a.get("method", "GET").upper()
                target_url = a.get("url") or url
                body = a.get("body", "")
                try:
                    if method == "GET":
                        r = await cli.get(target_url)
                    else:
                        r = await cli.request(method, target_url,
                                              content=body)
                    results.append({
                        "attack": a,
                        "status": r.status_code,
                        "body": r.text[:500],
                    })
                except Exception as e:  # noqa: BLE001
                    results.append({"attack": a, "error": str(e)})

        # LLM 判定
        prompt = (
            f"你是链路漏洞判定专家。基于攻击指令与响应，判定哪些是真实漏洞。\n\n"
            f"目标: {url}\n"
            f"攻击-响应:\n{json.dumps(results, ensure_ascii=False)}\n\n"
            f"判定规则:\n"
            f"  - 跳步成功（最终节点返回 200 + 业务数据）= 步骤绕过漏洞\n"
            f"  - 身份错位成功（用 B 的 token 看到 A 的数据）= 水平越权\n"
            f"  - 状态回退成功（已完成态被回滚）= 状态回退漏洞\n"
            f"输出 JSON 数组（只含真漏洞），每项: {{\"title\":\"\","
            f"\"vuln_type\":\"business_logic\",\"severity\":\"low/medium/high\","
            f"\"attack_type\":\"identity_swap/step_skip/state_rollback\","
            f"\"payload\":\"\",\"target_url\":\"\",\"detail\":\"\","
            f"\"evidence\":\"\",\"confidence\":0-1}}。只输出 JSON 数组。"
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
