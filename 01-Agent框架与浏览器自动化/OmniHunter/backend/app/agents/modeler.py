"""Modeler 业务建模 Agent（AI1）：基于静态文档/页面/接口文档搭初始业务模型。

职责（体系起点）：
  - 抓取目标页面 + 接口文档（优先 web_scrape，Firecrawl 转 markdown）
  - LLM 产出业务模型 JSON：business_rules / api_list / flows / hidden_params_hint
  - 沉淀进 Intel(kind="business_model", key=url)，命中缓存直接读不烧 token
  - 给 AI2 Attacker 提供基线业务规则与接口清单

缓存大法：同一站点同一套业务模型只分析一次，第二次直接召回复用。
"""
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class ModelerAgent(BaseAgent):
    role = "modeler"
    description = ("AI1 业务建模端：抓页面/接口文档→LLM 产出业务规则+接口清单+流程"
                  "+隐形参数提示，沉淀进 Intel 缓存复用，作体系起点。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router=None, pruning=None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event,
                         router=router, pruning=pruning)

    async def run(self, task_input: dict) -> dict:
        url = self.target.url
        # 缓存命中：同一站点业务模型只建模一次（缓存大法，不重复烧 token）
        cached = ""
        if self.memory:
            items = self.memory.recall(url, kind="business_model", limit=1)
            if items:
                cached = items[0].value
                self.think(f"命中业务模型缓存，直接复用（不重复烧 token）")
                self.memory.hit(items[0].id)
                return {"business_model": _safe_model(cached), "cached": True}

        # 抓取目标首页 / 接口文档（Firecrawl 转 LLM-friendly markdown）
        self.think(f"未命中缓存，开始抓取目标页面与接口文档: {url}")
        page_md = self.tools.execute("web_scrape", {"url": url})
        self.tool_call("web_scrape", {"url": url}, page_md[:800])

        # 尝试常见接口文档路径（Swagger/OpenAPI 等）
        api_doc = ""
        for path in ("/swagger-ui/index.html", "/v3/api-docs", "/api-docs",
                     "/openapi.json", "/docs"):
            doc_url = url.rstrip("/") + path
            out = self.tools.execute("web_scrape", {"url": doc_url})
            if "错误" not in out[:20] and "未配置" not in out[:20]:
                api_doc += f"\n--- {path} ---\n{out[:1500]}"
                break

        # === 2026-08-30 新增：规则层 0 Token 预筛（CMS 指纹 + 攻击模板 + 参数提取）===
        cms_result = {}
        extracted_params: dict = {}
        if self.router:
            combined_text = f"{page_md[:5000]}\n{api_doc[:3000]}"
            try:
                cms_result = self.router.dispatch("match_cms_fingerprint", combined_text)
                self.think(f"[规则层 0Token] CMS 指纹匹配: {cms_result.get('matched_cms')}, "
                            f"预置攻击模板 {len(cms_result.get('attack_templates', []))} 条")
            except Exception as exc:  # noqa: BLE001
                self.think(f"[规则层] CMS 匹配异常: {exc}")
            try:
                extracted_params = self.router.dispatch("extract_params", combined_text)
                self.think(f"[规则层 0Token] 抽取参数 "
                            f"{sum(len(v) for v in extracted_params.values()) if isinstance(extracted_params, dict) else 0} 个")
            except Exception as exc:  # noqa: BLE001
                self.think(f"[规则层] 参数提取异常: {exc}")

        system = self.system_prompt(
            "你是业务建模 Agent。基于抓取的页面 markdown + 接口文档，"
            "产出业务模型 JSON，字段：\n"
            "  business_rules: 业务规则清单（每条含 name/desc/影响接口）\n"
            "  api_list: 接口清单（method/path/params/auth_required/疑似越权风险）\n"
            "  flows: 核心业务流程（如 登录→下单→支付→退款，列出关键接口顺序）\n"
            "  hidden_params_hint: 文档未标注但可能参与服务端逻辑判断的隐形参数提示\n"
            "    （加密 token / cookie 隐含字段 / 状态校验位 / X-CSRF 等）\n"
            "  matched_cms: 规则层已识别的 CMS 类型列表（原样透传）\n"
            "  attack_templates: 基于 CMS 指纹的预置攻击模板提示（原样透传/补充）\n"
            "只输出 JSON，不要解释。"
        )
        prompt = (
            f"目标: {url}\n页面 markdown(截断):\n{page_md[:3000]}\n"
            f"接口文档(截断):\n{api_doc[:2000] or '无'}\n"
        )
        if cms_result:
            matched_cms = cms_result.get("matched_cms") or []
            attack_tpls = cms_result.get("attack_templates") or []
            prompt += (
                f"\n【规则层 0Token 预筛结果】\n"
                f"识别 CMS: {matched_cms}\n"
                f"预置攻击模板(请结合业务模型验证后写入 attack_templates):\n"
                f"  {attack_tpls}\n"
                f"请将以上 CMS 信息合并到业务模型的 matched_cms / attack_templates 字段，"
                f"不要浪费 token 重复识别。\n"
            )
        if extracted_params and isinstance(extracted_params, dict):
            prompt += (
                f"\n【规则层 0Token 参数预提取】\n"
                f"{json.dumps(extracted_params, ensure_ascii=False)[:600]}\n"
                f"请在 api_list.params 中结合文档补充细节，不要重复生成。\n"
            )
        prompt += "输出业务模型 JSON。"
        model = self.llm.chat_json([
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(model, dict):
            model = {"business_rules": [], "api_list": [],
                     "flows": [], "hidden_params_hint": []}
        # 兜底注入：LLM 哪怕忘了把规则层结果写回去，这里也强制合并（确保下游 100% 拿到）
        if cms_result:
            model.setdefault("matched_cms", cms_result.get("matched_cms") or ["unknown"])
            if cms_result.get("attack_templates"):
                existing = model.get("attack_templates") or []
                if not isinstance(existing, list):
                    existing = []
                for t in cms_result["attack_templates"]:
                    if t not in existing:
                        existing.append(t)
                model["attack_templates"] = existing
        if extracted_params and isinstance(extracted_params, dict):
            model.setdefault("extracted_params", extracted_params)

        # 沉淀进 Intel 缓存（kind=business_model），后续 Attacker / 下一轮迭代复用
        if self.memory:
            self.memory.store("business_model", url, json.dumps(model, ensure_ascii=False),
                              confidence=0.75, source=self.target.id)
            self.think("业务模型已沉淀进 Intel，下次同站直接复用")

        return {"business_model": model, "cached": False}


def _safe_model(text: str) -> dict:
    """从 Intel.value（字符串）安全还原业务模型 dict。"""
    if not text:
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"raw": text}
