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
from ..core.pruning import prioritize_actions
from ..core.tool_registry import ToolRegistry


class AttackTreeAgent(BaseAgent):
    role = "attack_tree"
    description = ("基于 site_profile + business_model 自动生成攻击树，"
                   "给 Attacker 提供结构化攻击路径，不凭空猜测。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router=None, pruning=None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event,
                         router=router, pruning=pruning)

    async def run(self, task_input: dict) -> dict:
        site_profile = task_input.get("site_profile", {})
        business_model = task_input.get("business_model", {})
        url = self.target.url

        self.think(f"生成攻击树: url={url}, "
                   f"subdomains={len(site_profile.get('subdomains', []))}, "
                   f"open_ports={len(site_profile.get('open_ports', []))}, "
                   f"api_list={len(business_model.get('api_list', []))}")

        # === 2026-08-30 新增：规则层 0Token 注入 CMS 预置攻击模板（0Token）===
        cms_templates: list[str] = []
        matched_cms: list[str] = []
        if self.router:
            cms_templates = (
                list(site_profile.get("cms_attack_templates") or [])
                + list(business_model.get("attack_templates") or [])
            )
            matched_cms = list(
                dict.fromkeys(
                    list(site_profile.get("matched_cms") or [])
                    + list(business_model.get("matched_cms") or [])
                )
            )
        # 去重并保留顺序
        cms_templates = list(dict.fromkeys([t for t in cms_templates if t]))
        self.think(f"[规则层 0Token] 合并 CMS={matched_cms}, "
                    f"预置攻击模板 {len(cms_templates)} 条，直接入树不用 LLM 重复猜")

        # LLM 基于资产清单 + 业务模型生成攻击树
        tree = self._llm_build_tree(
            site_profile, business_model, url,
            matched_cms=matched_cms, cms_templates=cms_templates,
        )
        # 规则层兜底：把 CMS 模板强制合成 leaf 分支（LLM 漏写时也保证有预置攻击动作）
        tree = self._inject_cms_leaves(tree, matched_cms, cms_templates)
        # 排序 priority_actions（剪枝策略公式，高价值动作先跑，提升命中率）
        try:
            tree["priority_actions"] = prioritize_actions(tree.get("priority_actions", []))
        except Exception as exc:  # noqa: BLE001
            self.think(f"[pruning] prioritize_actions 异常: {exc}")

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

    def _inject_cms_leaves(self, tree: dict, matched_cms: list[str],
                           cms_templates: list[str]) -> dict:
        """把规则层 CMS 预置模板合成 branch + leaf，保证 0Token 预置动作 100% 入树。"""
        if not cms_templates:
            return tree
        branches: list[dict] = tree.get("branches") or []
        if not isinstance(branches, list):
            branches = []
        existing_tpls = set()
        for br in branches:
            for leaf in (br.get("leaves") or []):
                existing_tpls.add(leaf.get("action", ""))
                existing_tpls.add(leaf.get("payload_hint", ""))
        new_leaves: list[dict] = []
        for tpl in cms_templates:
            if tpl in existing_tpls:
                continue
            new_leaves.append({
                "action": f"[0Token 预置] {tpl}",
                "tool": "httpx_probe_or_exploit",
                "payload_hint": tpl,
                "target_param": "",
                "success_signal": "状态码 200/返回敏感信息/越权数据",
                "success_rate": 0.7,
                "severity": "high",
                "needs_crypto_handling": False,
                "branch_id": "cms_templates",
            })
        if new_leaves:
            branch_index = max(0, len(branches) - 1)
            branches.append({
                "sub_goal": (f"CMS 预置漏洞验证（{', '.join(matched_cms) or '已识别'}）"),
                "precondition": "已通过 httpx 指纹识别出目标 CMS",
                "leaves": new_leaves,
            })
            tree["branches"] = branches
            priority: list[dict] = tree.get("priority_actions") or []
            if not isinstance(priority, list):
                priority = []
            for i, leaf in enumerate(new_leaves):
                priority.append({
                    "branch_index": branch_index,
                    "leaf_index": i,
                    "action": leaf["action"],
                    "tool": leaf["tool"],
                    "success_rate": leaf.get("success_rate", 0.7),
                    "severity": leaf.get("severity", "high"),
                    "target_param": leaf.get("target_param", ""),
                    "payload_hint": leaf.get("payload_hint", ""),
                })
            tree["priority_actions"] = priority
        return tree

    def _llm_build_tree(self, site_profile: dict,
                        business_model: dict, url: str,
                        matched_cms: list[str] | None = None,
                        cms_templates: list[str] | None = None) -> dict:
        """LLM 基于资产 + 业务模型生成攻击树 + 优先级动作清单。"""
        matched_cms = matched_cms or []
        cms_templates = cms_templates or []
        # 截断长字段避免 prompt 超长
        sp_brief = {
            "root_domain": site_profile.get("root_domain", ""),
            "subdomains_count": len(site_profile.get("subdomains", [])),
            "subdomains_sample": site_profile.get("subdomains", [])[:5],
            "open_ports": site_profile.get("open_ports", [])[:10],
            "fingerprint": (site_profile.get("fingerprint") or "")[:200],
            "web_entries_count": len(site_profile.get("web_entries", [])),
            "matched_cms": matched_cms,
            "discovered_urls_count": len(site_profile.get("discovered_urls") or []),
        }
        bm_brief = {
            "business_rules": business_model.get("business_rules", [])[:8],
            "api_list": business_model.get("api_list", [])[:10],
            "flows": business_model.get("flows", [])[:5],
            "hidden_params_hint": business_model.get("hidden_params_hint", [])[:5],
            "extracted_params": (
                {k: v for k, v in (business_model.get("extracted_params") or {}).items()}
                if isinstance(business_model.get("extracted_params"), dict) else {}
            ),
        }

        # 规则层：对攻击模板做 0Token 固定变异，产出预置动作直接给 LLM 参考（不用它凭空想）
        fixed_mutation_actions: list[dict] = []
        if self.router and bm_brief["extracted_params"]:
            try:
                mutations = self.router.dispatch(
                    "fixed_payload_mutation", bm_brief["extracted_params"])
                for m in mutations or []:
                    fixed_mutation_actions.append({
                        "action": (f"[0Token 固定变异] {m.get('intent', '')} "
                                   f"改参数 {m.get('param', '')} 为 {m.get('mutated', '')}"),
                        "tool": "httpx_replay",
                        "payload_hint": (f"{m.get('type', '')}: {m.get('param', '')}="
                                         f"{m.get('mutated', '')}"),
                        "target_param": m.get("param", ""),
                        "success_signal": "越权数据 / 负数价格生效 / 状态被篡改",
                        "success_rate": 0.65,
                        "severity": "high",
                        "needs_crypto_handling": False,
                    })
                self.think(f"[规则层 0Token] 固定变异预置动作 {len(fixed_mutation_actions)} 条")
            except Exception as exc:  # noqa: BLE001
                self.think(f"[规则层] fixed_payload_mutation 异常: {exc}")

        prompt = (
            f"你是资深攻击树设计专家，借鉴 Shannon white-box attack planning。\n"
            f"基于目标资产清单 + 业务模型，生成结构化攻击树，给后续 Attacker 提供路径。\n\n"
            f"目标: {url}\n"
            f"资产清单(简): {json.dumps(sp_brief, ensure_ascii=False)}\n"
            f"业务模型(简): {json.dumps(bm_brief, ensure_ascii=False)}\n\n"
        )
        if matched_cms or cms_templates:
            prompt += (
                f"\n【规则层 0Token 预置 CMS 信息（请直接使用，不要重复识别，省 token）】\n"
                f"已识别 CMS: {matched_cms}\n"
                f"预置攻击模板（请作为最高优先级分支的叶子动作写入）:\n"
                f"  {json.dumps(cms_templates, ensure_ascii=False)}\n"
            )
        if fixed_mutation_actions:
            prompt += (
                f"\n【规则层 0Token 固定变异动作（请写入 leaves/priority_actions，省 LLM 凭空猜）】\n"
                f"{json.dumps(fixed_mutation_actions, ensure_ascii=False)}\n"
            )
        prompt += (
            f"\n重点覆盖企业 + 教育高频漏洞类型：\n"
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
            f"          \"success_rate\": 0-1,\n"
            f"          \"severity\": \"info/low/medium/high/critical\",\n"
            f"          \"needs_crypto_handling\": false,\n"
            f"          \"branch_id\": \"分支ID字符串（用于剪枝，如 auth_bypass / idor / cms_xxx）\"\n"
            f"        }}\n"
            f"      ]\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"priority_actions\": [\n"
            f"    输出扁平数组，每项含 branch_index/leaf_index/action/tool/success_rate/severity/"
            f"target_param/payload_hint/branch_id\n"
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
