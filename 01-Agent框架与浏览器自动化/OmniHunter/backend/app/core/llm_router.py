"""LLM 分层路由：把任务拆成三层，按需调不同能力模型，Token 消耗砍半。

用户优化建议：不要什么都靠大模型，能规则解决的不用小模型，
能小模型解决的不用大模型，把 Token 花在最有价值的决策节点。

三层架构：
  - 规则层（0 Token）：流量清洗、参数提取、常见 CMS 指纹匹配、
    固定 payload 变异，全部用 Python 规则实现，完全不调 LLM
  - 小模型层（低 Token）：参数语义识别、简单攻击策略生成、
    响应初步判断，用 7B 级本地模型（如 Qwen2-7B）或轻量 API
  - 大模型层（高 Token）：仅在攻击树生成、漏洞语义判定、
    报告撰写三个关键节点调用，只做决策不做体力活

路由策略：根据 task_type 自动决定走哪层。
"""
import json
import re
from typing import Any, Callable

from .llm import LLMClient


# 任务类型 -> 路由层级
TASK_ROUTING: dict[str, str] = {
    # 规则层（0 Token）— 纯 Python 实现
    "extract_params": "rule",          # 从流量提取参数名/值
    "extract_urls": "rule",            # 提取 URL 清单
    "match_cms_fingerprint": "rule",   # CMS 指纹匹配（强智/正方/泛微/用友）
    "fixed_payload_mutation": "rule",  # 固定 payload 变异（IDOR/负价格/跳步）
    "filter_static_resources": "rule", # 过滤静态资源请求
    "strip_request_headers": "rule",   # 剥离冗余请求头压缩上下文

    # 小模型层（低 Token）
    "param_semantic_classify": "small",  # 参数语义分类（user_id=身份类/price=数值类）
    "simple_attack_strategy": "small",   # 简单攻击策略生成
    "response_preliminary_judge": "small",  # 响应初步判断（200/异常/敏感词）

    # 大模型层（高 Token）
    "attack_tree_generation": "large",   # 攻击树生成
    "vuln_semantic_judge": "large",       # 漏洞语义判定
    "business_model_building": "large",   # 业务建模
    "report_writing": "large",            # 报告撰写
    "chain_identification": "large",       # 链路识别
}


class LLMRouter:
    """LLM 分层路由器：按 task_type 自动走规则/小模型/大模型三层。

    用法（Agent 内部）：
        router = LLMRouter(settings, big_llm=llm)
        result = router.dispatch("extract_params", traffic_text)
        # extract_params 走规则层 0 Token 直接返回
        result = router.dispatch("attack_tree_generation", ctx)
        # attack_tree 走大模型层
    """

    def __init__(self, settings,
                 big_llm: LLMClient | None = None,
                 small_llm: LLMClient | None = None):
        self.settings = settings
        self.big_llm = big_llm  # 大模型（高 Token，关键决策）
        self.small_llm = small_llm or big_llm  # 小模型兜底用大模型
        self._rule_handlers: dict[str, Callable[..., Any]] = {
            "extract_params": _rule_extract_params,
            "extract_urls": _rule_extract_urls,
            "match_cms_fingerprint": _rule_match_cms,
            "fixed_payload_mutation": _rule_fixed_mutation,
            "filter_static_resources": _rule_filter_static,
            "strip_request_headers": _rule_strip_headers,
        }
        # 统计：各层调用次数 + 估算省下的 Token
        self.stats: dict[str, dict] = {
            "rule": {"calls": 0, "saved_tokens": 0},
            "small": {"calls": 0, "saved_tokens": 0},
            "large": {"calls": 0, "saved_tokens": 0},
        }

    def dispatch(self, task_type: str, *args, **kwargs) -> Any:
        """按 task_type 路由到对应层。"""
        layer = TASK_ROUTING.get(task_type, "large")  # 未知任务走大模型兜底

        if layer == "rule":
            handler = self._rule_handlers.get(task_type)
            if handler:
                self.stats["rule"]["calls"] += 1
                # 规则层省下 ~500 token/次（小模型）到 ~2000 token/次（大模型）
                self.stats["rule"]["saved_tokens"] += 1500
                return handler(*args, **kwargs)

        if layer == "small":
            self.stats["small"]["calls"] += 1
            # 小模型省下 ~1500 token/次（相对大模型）
            self.stats["small"]["saved_tokens"] += 1500
            return self._call_small(task_type, *args, **kwargs)

        # 大模型
        self.stats["large"]["calls"] += 1
        return self._call_large(task_type, *args, **kwargs)

    def _call_small(self, task_type: str, *args, **kwargs) -> Any:
        """小模型层调用（prompt 精简，max_tokens 限制）。"""
        prompt = kwargs.get("prompt") or (args[0] if args else "")
        if not prompt:
            return {}
        # 小模型：精简 prompt + 限制输出长度
        compact_prompt = _compact_prompt(prompt)
        if self.small_llm:
            return self.small_llm.chat_json([
                {"role": "system",
                 "content": "你是轻量分析模型，简洁回答，只输出 JSON。"},
                {"role": "user", "content": compact_prompt[:2000]},
            ])
        return {"error": "small llm 未配置"}

    def _call_large(self, task_type: str, *args, **kwargs) -> Any:
        """大模型层调用（关键决策节点）。"""
        prompt = kwargs.get("prompt") or (args[0] if args else "")
        if not prompt:
            return {}
        if self.big_llm:
            return self.big_llm.chat_json([
                {"role": "system", "content": "你是资深安全专家，只输出 JSON。"},
                {"role": "user", "content": prompt},
            ])
        return {"error": "big llm 未配置"}

    def stats_summary(self) -> dict:
        """路由统计（前端展示省了多少 Token）。"""
        return self.stats


# ===== 规则层实现（0 Token）=====

def _rule_extract_params(traffic_text: str, *_args, **_kwargs) -> dict:
    """规则层：从流量文本提取参数名/值（不调 LLM）。

    匹配 ?key=value&key2=value2 / JSON body / form-encoded。
    """
    params: dict[str, list[str]] = {"query": [], "body": [], "header": []}

    # URL query 参数
    for m in re.finditer(r"[?&]([^=&\s]+)=([^&\s#]+)", traffic_text):
        params["query"].append({"name": m.group(1), "value": m.group(2)[:100]})

    # JSON body 参数（"key":"value" 或 "key":number）
    for m in re.finditer(r'"([^"]+)"\s*:\s*"?([^",}\s]+)"?', traffic_text):
        name = m.group(1)
        if name in ("data", "result", "code", "msg", "message", "status"):
            continue
        params["body"].append({"name": name, "value": m.group(2)[:100]})

    # 去重
    for k in params:
        seen = set()
        unique = []
        for p in params[k]:
            if p["name"] not in seen:
                unique.append(p)
                seen.add(p["name"])
        params[k] = unique[:30]

    return params


def _rule_extract_urls(traffic_text: str, *_args, **_kwargs) -> list[str]:
    """规则层：从流量提取 URL 清单（去重 + 过滤静态资源）。"""
    urls = set()
    for m in re.finditer(r'https?://[^\s<>"\']+', traffic_text):
        u = m.group(0).rstrip(".,;)")
        if not _is_static_resource(u):
            urls.add(u)
    return sorted(urls)[:50]


def _rule_match_cms(traffic_text: str, *_args, **_kwargs) -> dict:
    """规则层：CMS 指纹匹配（教育 + 企业高频系统）。

    内置常见教务/OA/电商系统指纹，匹配到直接返回 CMS 类型，
    不调 LLM。
    """
    fingerprints = {
        # 教务系统
        "正方教务": [r"zfsoft", r"正方", r"教务管理系统"],
        "强智教务": [r"qzsoft", r"强智", r"qz_jw"],
        "青果教务": [r"青果", r"qingguo"],
        "URP综合教务": [r"urp", r"综合教务"],
        # 企业 OA
        "泛微 e-cology": [r"e-cology", r"weaver", r"泛微"],
        "致远 OA": [r"seeyon", r"致远", r"A8"],
        "用友 NC": [r"yonyou", r"用友", r"nccloud"],
        "用友 U8": [r"u8", r"ufsoft"],
        "通达 OA": [r"tongda", r"tdoa"],
        "蓝凌 OA": [r"landray", r"蓝凌"],
        # 电商
        "Ecshop": [r"ecshop", r"ECSHOP"],
        "ShopEx": [r"shopex"],
        "Discuz": [r"discuz", r"Crossday"],
        "PHPCMS": [r"phpcms"],
        "织梦 CMS": [r"dedecms", r"织梦"],
        # 框架
        "Spring Boot": [r"X-Application-Context.*spring",
                         r"Whitelabel Error Page"],
        "Struts2": [r"struts2", r"org.apache.struts"],
        "ThinkPHP": [r"thinkphp", r"ThinkPHP"],
    }
    matched = []
    for cms, patterns in fingerprints.items():
        for p in patterns:
            if re.search(p, traffic_text, re.IGNORECASE):
                matched.append(cms)
                break
    return {"matched_cms": matched[:5] or ["unknown"],
            "attack_templates": _cms_attack_templates(matched)}


def _cms_attack_templates(cms_list: list[str]) -> list[str]:
    """CMS 对应的预置攻击模板提示（命中即用预置规则，0 Token）。"""
    templates = {
        "泛微 e-cology": ["WorkflowCenterTree / 未授权", "weaver 任意文件上传",
                          "DBconfigReader SQL 注入"],
        "致远 OA": ["A8 htmlofficeservlet 任意文件", "status.jsp 信息泄露",
                     "ajaxAction 文件上传"],
        "用友 NC": ["nccloud 任意文件上传", "UClientConfig 信息泄露"],
        "通达 OA": ["data@oa 未授权", "general/report 任意文件包含"],
        "正方教务": ["xsxj 登录绕过", "xsxk 越权查成绩"],
        "强智教务": ["qz_jw 越权", "student 任意文件下载"],
        "织梦 CMS": ["plus/search SQL 注入", "include/dedesql 注入"],
        "Discuz": ["uc.php SQL 注入", "portal.php XSS"],
        "ThinkPHP": ["rce 远程代码执行（5.0.x/5.1.x）",
                      "index.php method rce"],
    }
    out = []
    for cms in cms_list:
        if cms in templates:
            out.extend(templates[cms])
    return out[:10]


def _rule_fixed_mutation(params_text: str, *_args, **_kwargs) -> list[dict]:
    """规则层：固定 payload 变异（不调 LLM）。

    对 user_id/order_id/stu_id 类参数做 IDOR 变异，
    对 price/amount/count 类做负值/极大值变异，
    对 status/state 做状态篡改。
    """
    mutations: list[dict] = []
    # 从 params_text 提取参数（容忍 dict 或 str 输入）
    params = []
    if isinstance(params_text, dict):
        for k, v in params_text.items():
            if isinstance(v, list):
                params.extend(v)
            else:
                params.append({"name": k, "value": str(v)})
    elif isinstance(params_text, str):
        for m in re.finditer(r'"?(\w+)"?\s*[:=]\s*"?(\w+)"?', params_text):
            params.append({"name": m.group(1), "value": m.group(2)})

    id_keywords = ("user_id", "uid", "stu_id", "student_id", "order_id",
                    "oid", "member_id", "account_id", "cid", "id")
    num_keywords = ("price", "amount", "count", "num", "quantity",
                     "money", "fee", "total", "score", "point")
    status_keywords = ("status", "state", "step", "stage", "phase")

    for p in params:
        name = p.get("name", "").lower()
        val = p.get("value", "")
        if not name or not val:
            continue
        # IDOR 变异：身份类参数改值
        if any(k in name for k in id_keywords):
            try:
                num = int(re.sub(r"\D", "", val) or "0")
            except Exception:  # noqa: BLE001
                num = 1
            mutations.append({
                "type": "idor", "param": name,
                "original": val, "mutated": str(num + 1),
                "intent": "水平越权测他人数据",
            })
            mutations.append({
                "type": "idor", "param": name,
                "original": val, "mutated": str(max(1, num - 1)),
                "intent": "反向 ID 越权",
            })
        # 数值类变异
        elif any(k in name for k in num_keywords):
            mutations.append({
                "type": "numeric_boundary", "param": name,
                "original": val, "mutated": "-1",
                "intent": "负值测后端范围校验",
            })
            mutations.append({
                "type": "numeric_boundary", "param": name,
                "original": val, "mutated": "0",
                "intent": "零值测边界",
            })
            mutations.append({
                "type": "numeric_boundary", "param": name,
                "original": val, "mutated": "99999999",
                "intent": "极大值测溢出",
            })
        # 状态类变异
        elif any(k in name for k in status_keywords):
            mutations.append({
                "type": "status_tamper", "param": name,
                "original": val, "mutated": "1",
                "intent": "状态篡改到已通过",
            })
            mutations.append({
                "type": "status_tamper", "param": name,
                "original": val, "mutated": "0",
                "intent": "状态回退到初始",
            })

    return mutations[:15]


def _rule_filter_static(traffic_text: str, *_args, **_kwargs) -> str:
    """规则层：过滤静态资源请求（不调 LLM）。"""
    static_ext = (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
                   ".ico", ".woff", ".woff2", ".ttf", ".mp4", ".mp3",
                   ".webp", ".map")
    lines = traffic_text.splitlines() if isinstance(traffic_text, str) else []
    kept = []
    for ln in lines:
        if not ln.strip():
            continue
        # 检查是否含静态资源 URL
        if any(ext in ln.lower() for ext in static_ext):
            continue
        kept.append(ln)
    return "\n".join(kept)


def _rule_strip_headers(traffic_text: str, *_args, **_kwargs) -> str:
    """规则层：剥离冗余请求头压缩上下文（不调 LLM）。

    只保留关键 headers（Authorization/Cookie/X-Token/Content-Type），
    剔除 User-Agent/Accept/Accept-Language 等无关字段。
    """
    key_headers = ("authorization", "cookie", "x-token", "x-csrf-token",
                    "x-auth-token", "content-type", "referer", "origin")
    if not isinstance(traffic_text, str):
        return traffic_text
    lines = traffic_text.splitlines()
    kept = []
    for ln in lines:
        ln_stripped = ln.strip()
        if not ln_stripped:
            kept.append(ln)
            continue
        # 检查是否 header 行（形如 Key: value）
        if ":" in ln_stripped and not ln_stripped.startswith(("GET", "POST",
                                                              "PUT", "DELETE",
                                                              "PATCH", "HEAD")):
            header_name = ln_stripped.split(":", 1)[0].lower().strip()
            if header_name not in key_headers:
                continue
        kept.append(ln)
    return "\n".join(kept)


def _compact_prompt(prompt: str) -> str:
    """压缩 prompt（小模型层用）：去掉多余换行 + 精简指令。"""
    # 压缩多换行
    compacted = re.sub(r"\n{3,}", "\n\n", prompt)
    # 去掉前后空白
    return compacted.strip()


def _is_static_resource(url: str) -> bool:
    """判断 URL 是否静态资源。"""
    static_ext = (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
                   ".ico", ".woff", ".woff2", ".ttf", ".mp4", ".mp3",
                   ".webp", ".map")
    url_lower = url.lower().split("?")[0]
    return any(url_lower.endswith(ext) for ext in static_ext)
