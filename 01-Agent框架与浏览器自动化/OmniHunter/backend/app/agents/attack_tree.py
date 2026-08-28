"""Attack Tree 自动生成 Agent。

用户需求：「单站深挖加一个环节，自动生成攻击树」——在 Attacker 多轮
攻击之前，先基于 site_profile + business_model 自动生成攻击路径树，
让 Attacker 不凭空猜测，按树节点顺序逐个推进攻击。

攻击树结构（借鉴 Shannon white-box attack planning + 攻击树标准范式）：
  root       : 目标总目标（如「拿到管理员权限 / 越权他人订单」）
  branches   : 子目标（如「获取 admin token」「绕过支付校验」）
  leaves     : 具体攻击动作（含 tool/payload_hint/前置条件/precondition）

输出树结构 + 按优先级排序的攻击动作清单，沉淀进 Intel(kind="attack_tree")。
"""
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class AttackTreeAgent(BaseAgent):
    role = "attack_tree"
    description = ("基于 site_profile + business_model 自动生成攻击树，"
                   "给 Attacker 提供结构化攻击路径，不凭空猜测。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        site_profile = task_input.get("site_profile", {})
        business_model = task_input.get("business_model", {})
        url = self.target.url

        self.think(f"生成攻击树: url={url}, "
                   f"subdomains={len(site_profile.get('subdomains', []))}, "
                   f"open_ports={len(site_profile.get('open_ports', []))}, "
                   f"api_list={len(business_model.get('api_list', []))}")

        # LLM 基于资产清单 + 业务模型生成攻击树
        tree = self._llm_build_tree(site_profile, business_model, url)
        self.think(f"攻击树根目标: {tree.get('root_goal', '')}, "
                   f"分支数: {len(tree.get('branches', []))}, "
                   f"叶子动作: {len(tree.get('priority_actions', []))}")

        # 沉淀 attack_tree 进记忆（下次同站直接复用）
        if self.memory:
            root_domain = site_profile.get("root_domain") or url
            self.memory.store("attack_tree", root_domain,
                              json.dumps(tree, ensure_ascii=False),
                              confidence=0.75,
                              source=f"attack_tree:{self.target.id}")
            self.think(f"沉淀 attack_tree 进记忆 root={root_domain}")

        return {"attack_tree": tree}

    def _llm_build_tree(self, site_profile: dict,
                        business_model: dict, url: str) -> dict:
        """LLM 基于资产 + 业务模型生成攻击树 + 优先级动作清单。"""
        # 截断长字段避免 prompt 超长
        sp_brief = {
            "root_domain": site_profile.get("root_domain", ""),
            "subdomains_count": len(site_profile.get("subdomains", [])),
            "subdomains_sample": site_profile.get("subdomains", [])[:5],
            "open_ports": site_profile.get("open_ports", [])[:10],
            "fingerprint": (site_profile.get("fingerprint") or "")[:200],
            "web_entries_count": len(site_profile.get("web_entries", [])),
        }
        bm_brief = {
            "business_rules": business_model.get("business_rules", [])[:8],
            "api_list": business_model.get("api_list", [])[:10],
            "flows": business_model.get("flows", [])[:5],
            "hidden_params_hint": business_model.get("hidden_params_hint", [])[:5],
        }

        prompt = (
            f"你是资深攻击树设计专家，借鉴 Shannon white-box attack planning。\n"
            f"基于目标资产清单 + 业务模型，生成结构化攻击树，给后续 Attacker 提供路径。\n\n"
            f"目标: {url}\n"
            f"资产清单(简): {json.dumps(sp_brief, ensure_ascii=False)}\n"
            f"业务模型(简): {json.dumps(bm_brief, ensure_ascii=False)}\n\n"
            f"重点覆盖企业 + 教育高频漏洞类型：\n"
            f"  - 权限越权（水平/垂直）\n"
            f"  - 未授权 API 访问\n"
            f"  - 硬编码凭证\n"
            f"  - 业务链路步骤绕过\n"
            f"  - 数值边界校验（负价格/极大值）\n"
            f"  - 加密参数变异（若有加密参数，标注需 crypto_tool 处理）\n\n"
            f"输出 JSON: {{\n"
            f"  \"root_goal\": \"总体攻击目标\",\n"
            f"  \"branches\": [\n"
            f"    {{\n"
            f"      \"sub_goal\": \"子目标\",\n"
            f"      \"precondition\": \"前置条件\",\n"
            f"      \"leaves\": [\n"
            f"        {{\n"
            f"          \"action\": \"具体攻击动作\",\n"
            f"          \"tool\": \"调用的工具名\",\n"
            f"          \"payload_hint\": \"payload 提示\",\n"
            f"          \"target_param\": \"攻击的参数或端点\",\n"
            f"          \"success_signal\": \"成功标志\",\n"
            f"          \"success_rate\": 0-1,  # 成功率预估\n"
            f"          \"severity\": \"info/low/medium/high/critical\",  # 危害等级\n"
            f"          \"needs_crypto_handling\": false  # 是否需 crypto_tool 解密重加密\n"
            f"        }}\n"
            f"      ]\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"priority_actions\": [\n"
            f"    按「success_rate*0.4 + severity*0.6」排序，输出扁平数组，"
            f"每项含 branch_index/leaf_index/action/tool/success_rate/severity\n"
            f"  ]\n"
            f"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            return {"root_goal": "未生成", "branches": [], "priority_actions": []}

        # 规范化兜底
        out.setdefault("root_goal", "未指定总体目标")
        out.setdefault("branches", [])
        out.setdefault("priority_actions", [])
        if not isinstance(out["branches"], list):
            out["branches"] = []
        if not isinstance(out["priority_actions"], list):
            out["priority_actions"] = []
        return out
