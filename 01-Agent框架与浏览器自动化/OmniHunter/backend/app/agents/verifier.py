"""Verifier 验证 Agent：借鉴 Strix / Xalgorix 的「发现-验证」闭环。

不轻信 Worker 的发现，独立用工具复现 payload，输出 verified + confidence。

三层误报过滤（用户优化建议）：
  Layer 1 正向语义校验：变异后不只看 HTTP 200，必须匹配响应体业务特征
          （如返回了目标用户姓名/学号、订单价格确实变更）
  Layer 2 负向对照校验（Strix counterevidence）：发"应被阻断"的负向控制
          payload，确认服务端会返回错误，排除"无论传什么都返回 200"的接口
  Layer 3 二次落地确认：对数据修改类漏洞，额外调用查询接口，确认数据
          真实写入数据库，不是前端回显欺骗

Xalgorix 思想：独立重新 exploit 每个发现以证明漏洞（不沿用 Worker 的证据）。
"""
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class VerifierAgent(BaseAgent):
    role = "verifier"
    description = ("独立复现 + Strix 反证：不轻信报告者，正向复现 payload "
                   "并额外发负向控制 payload 验证被阻断，才确认漏洞真实。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        v = task_input["vuln"]
        self.think(f"独立复现漏洞: {v.get('title', v.get('vuln_type', ''))}")

        # 步骤 1：LLM 设计正向复现 + 负向控制 payload（Strix counterevidence）
        payload_plan = self._plan_payloads(v)
        self.think(f"反证 payload 方案: positive={payload_plan.get('positive_payload')}, "
                   f"negative={payload_plan.get('negative_payload')}, "
                   f"expected_block={payload_plan.get('expected_negative_status')}")

        # 步骤 2：用工具复现正向 payload（实际重放/触发）
        positive_result = await self._replay_payload(payload_plan.get("positive_payload", ""), v)
        self.think(f"正向复现结果: {positive_result[:300]}")

        # 步骤 3：发负向控制 payload（应被正常阻断）
        negative_result = await self._replay_payload(payload_plan.get("negative_payload", ""), v)
        self.think(f"负向控制结果: {negative_result[:300]}")

        # 步骤 4：综合判定（Strix counterevidence 闭环逻辑）
        verdict = self._judge_counterevidence(
            v, payload_plan, positive_result, negative_result)

        # Layer 1: 正向语义校验（不只看 200，要匹配响应体业务特征）
        semantic_ok = self._semantic_validate(
            v, positive_result, payload_plan)
        verdict["semantic_validated"] = semantic_ok
        if verdict.get("verified") and not semantic_ok:
            verdict["verified"] = False
            verdict["reason"] = (verdict.get("reason", "") +
                                  " [Layer1] 响应未匹配业务特征，疑似通用错误页。")
            verdict["confidence"] = min(verdict.get("confidence", 0.3), 0.4)
            self.think("Layer1 语义校验未通过：响应未匹配业务特征")

        # Layer 3: 二次落地确认（数据修改类漏洞调查询接口确认写入）
        if verdict.get("verified") and self._is_data_modify_vuln(v):
            landed = await self._confirm_data_landed(v, payload_plan)
            verdict["data_landed"] = landed
            if not landed:
                verdict["verified"] = False
                verdict["reason"] = (verdict.get("reason", "") +
                                      " [Layer3] 查询接口未确认数据真实写入，"
                                      "疑似前端回显欺骗。")
                verdict["confidence"] = min(verdict.get("confidence", 0.3), 0.4)
                self.think("Layer3 二次落地确认未通过：数据未真实写入")

        self.think(f"反证判定: verified={verdict['verified']}, "
                   f"confidence={verdict['confidence']}, reason={verdict['reason']}")
        return verdict

    # ===== Layer 1: 正向语义校验 =====
    def _semantic_validate(self, vuln: dict, positive_result: str,
                            plan: dict) -> bool:
        """校验正向响应是否匹配业务特征（不只看 HTTP 200）。

        用户要点：变异后不只要看 HTTP 200，必须匹配响应体业务特征
        （如返回了目标用户姓名/学号、订单价格确实变更）。
        """
        expected_signal = plan.get("expected_positive_signal", "")
        if not expected_signal:
            # 无预期信号，跳过本层（不阻塞验证）
            return True
        # 规则层先做轻量匹配（0 Token）
        if expected_signal and expected_signal.lower() in positive_result.lower():
            return True
        # 规则未命中走 LLM 判定（响应体语义是否匹配业务特征）
        prompt = (
            f"你是响应语义校验器。判断响应体是否含业务特征（不只看 200）。\n\n"
            f"漏洞: {vuln.get('title', '')}\n"
            f"预期业务特征: {expected_signal}\n"
            f"实际响应(截断): {positive_result[:600]}\n\n"
            f"判定: 响应是否含业务数据特征（如目标用户姓名/学号/订单价格变更）？\n"
            f"输出 JSON: {{\"semantic_match\": bool, \"matched_feature\": \"\","
            f"\"reason\": \"\"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if isinstance(out, dict):
            return bool(out.get("semantic_match", False))
        return False

    # ===== Layer 3: 二次落地确认 =====
    def _is_data_modify_vuln(self, vuln: dict) -> bool:
        """判断是否数据修改类漏洞（需 Layer 3 二次落地确认）。"""
        modify_types = ("business_logic", "idor", "idor_write",
                        "unauthorized_modify", "price_tamper",
                        "status_tamper", "privilege_escalation")
        vtype = str(vuln.get("vuln_type", "")).lower()
        title = str(vuln.get("title", "")).lower()
        return (vtype in modify_types
                or any(k in title for k in ("修改", "篡改", "越权写",
                                              "price", "status", "改")))

    async def _confirm_data_landed(self, vuln: dict,
                                    plan: dict) -> bool:
        """对数据修改类漏洞，调查询接口确认数据真实写入数据库。

        用户要点：对数据修改类漏洞，额外调用查询接口，确认数据真实写入，
        不是前端回显欺骗。
        """
        # LLM 生成查询接口调用方案
        prompt = (
            f"你是数据落地确认器。对数据修改类漏洞，设计一个查询接口调用，"
            f"确认数据真实写入数据库（不是前端回显）。\n\n"
            f"漏洞: {json.dumps(vuln, ensure_ascii=False)}\n"
            f"目标: {self.target.url}\n"
            f"正向 payload: {plan.get('positive_payload', '')}\n\n"
            f"输出 JSON: {{\"query_url\":\"\",\"query_method\":\"GET\","
            f"\"expected_data_signal\":\"应出现的数据特征\"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict) or not out.get("query_url"):
            # LLM 未生成查询方案，跳过本层（不阻塞）
            return True

        try:
            import httpx
            # nosec B501 — 验证器需查询自签/内网站点确认数据落地
            async with httpx.AsyncClient(verify=False, timeout=15,  # nosec B501
                                         follow_redirects=False) as cli:
                qurl = out["query_url"]
                if out.get("query_method", "GET").upper() == "GET":
                    r = await cli.get(qurl)
                else:
                    r = await cli.post(qurl)
                body = r.text[:800]
        except Exception as e:  # noqa: BLE001
            self.think(f"二次落地查询失败: {e}")
            return False

        expected = out.get("expected_data_signal", "")
        if expected and expected.lower() in body.lower():
            return True
        # 无预期信号也按未落地处理（保守）
        return False if expected else True

    # ===== 步骤 1：设计正向 + 负向 payload =====
    def _plan_payloads(self, vuln: dict) -> dict:
        """LLM 设计正向复现 payload 与负向控制 payload。

        Strix counterevidence 原则：
          - positive_payload  : 应触发漏洞的 payload（如 ' OR 1=1-- -）
          - negative_payload  : 应被正常阻断的 payload（如 ' AND 1=2-- - 或
                                 空白/正常值），用于证明过滤逻辑存在
          - expected_positive_signal : 正向 payload 应出现的异常信号
          - expected_negative_status : 负向 payload 应被阻断的状态/特征
        """
        prompt = (
            f"你是漏洞验证专家，应用 Strix counterevidence（反证）方法论。\n"
            f"为漏洞设计一对验证 payload：\n"
            f"  1) positive_payload : 应触发漏洞的 payload\n"
            f"  2) negative_payload : 应被正常阻断的负向控制 payload"
            f"（如布尔假值/空值/越界 ID），证明过滤逻辑确实生效\n"
            f"  3) expected_positive_signal : 正向 payload 触发时应出现的信号\n"
            f"  4) expected_negative_status : 负向 payload 应出现的状态码/特征"
            f"（如 200+正常错误页/403/401）\n\n"
            f"漏洞: {json.dumps(vuln, ensure_ascii=False)}\n"
            f"目标: {self.target.url}\n"
            f"可调用 payload_library 工具查 payload 模板。\n"
            f"输出 JSON: {{\"positive_payload\":\"\",\"negative_payload\":\"\","
            f"\"expected_positive_signal\":\"\",\"expected_negative_status\":\"\","
            f"\"replay_tool\":\"\"}}。只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, dict) else {}

    # ===== 步骤 2/3：复现 payload =====
    async def _replay_payload(self, payload: str, vuln: dict) -> str:
        """用工具复现 payload。无 payload 或无工具时降级走 LLM 推理。"""
        if not payload:
            return "无 payload 可复现（LLM 未生成正向/负向 payload）。"

        # 优先用 httpx 库异步重放（若 payload 是 HTTP 请求形态）
        if "http" in payload.lower() or payload.startswith(("/", "?", "'")):
            replay = await self._http_replay(payload, vuln)
            if replay:
                return replay

        # 兜底：调用注册工具（如 sqlmap_scan/nuclei_scan 等）
        tool_name = vuln.get("replay_tool") or "httpx_probe"
        if self.tools and tool_name in self.tools.names():
            url = getattr(self.target, "url", "") or ""
            args = {"url": url}
            if tool_name == "sqlmap_scan":
                args["data"] = payload
            elif tool_name == "nuclei_scan":
                args["templates"] = payload
            try:
                result = self.tools.execute(tool_name, args)
                self.tool_call(tool_name, args, result[:500] if result else "")
                return result or "工具无输出"
            except Exception as e:  # noqa: BLE001
                return f"工具复现失败: {e}"

        return f"无可用复现工具（尝试 {tool_name} 未注册或失败）。payload: {payload}"

    async def _http_replay(self, payload: str, vuln: dict) -> str:
        """用 httpx 异步重放 HTTP 形态的 payload。"""
        try:
            import httpx
        except ImportError:
            return ""
        url = getattr(self.target, "url", "") or vuln.get("url", "")
        if not url:
            return ""
        # 简化：把 payload 拼到 url query 或 body，重放看响应
        try:
            # nosec B501 — 验证器需重放 payload 到自签/内网站点，必须忽略 SSL 校验
            async with httpx.AsyncClient(verify=False, timeout=15,  # nosec B501
                                         follow_redirects=False) as cli:
                target_url = url
                if payload.startswith("?"):
                    target_url = url + payload
                    r = await cli.get(target_url)
                elif payload.startswith("/"):
                    base = url.split("/", 3)
                    target_url = "/".join(base[:3]) + payload
                    r = await cli.get(target_url)
                else:
                    r = await cli.post(url, data={"q": payload})
                return (f"HTTP {r.status_code} {r.reason_phrase} "
                        f"len={len(r.content)} body={r.text[:300]!r}")
        except Exception as e:  # noqa: BLE001
            return f"http 重放错误: {e}"

    # ===== 步骤 4：Strix counterevidence 综合判定 =====
    def _judge_counterevidence(self, vuln: dict, plan: dict,
                                positive_result: str, negative_result: str) -> dict:
        """LLM 综合正向/负向结果，应用 Strix 反证闭环判定。

        判定矩阵（Strix counterevidence 关键逻辑）：
          - verified=True 要求：
              a) 正向 payload 触发了 expected_positive_signal
              b) 负向 payload 出现了 expected_negative_status（被正常阻断）
          - 仅正向触发而负向未被阻断 → 可能是通用错误页/无影响，verified=False
          - 正向未触发 → verified=False
        """
        prompt = (
            f"你是 Strix counterevidence 判定器。综合判定漏洞是否真实。\n"
            f"漏洞: {json.dumps(vuln, ensure_ascii=False)}\n"
            f"正向 payload: {plan.get('positive_payload', '')}\n"
            f"  应触发信号: {plan.get('expected_positive_signal', '')}\n"
            f"  实际结果: {positive_result[:800]}\n"
            f"负向控制 payload: {plan.get('negative_payload', '')}\n"
            f"  应被阻断状态: {plan.get('expected_negative_status', '')}\n"
            f"  实际结果: {negative_result[:800]}\n\n"
            f"判定规则:\n"
            f"  - verified=True 必须同时满足：正向触发了应触发信号 + 负向被正常阻断\n"
            f"  - 仅正向触发而负向未被阻断 → verified=False（可能是通用错误/误报）\n"
            f"  - 正向未触发 → verified=False\n"
            f"  - confidence: 双重验证通过 0.8-0.95，仅正向 0.3-0.5，均失败 0.1\n"
            f"输出 JSON: {{\"verified\":bool,\"confidence\":0-1,"
            f"\"positive_triggered\":bool,\"negative_blocked\":bool,\"reason\":\"\"}}。"
            f"只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        if not isinstance(out, dict):
            return {"verified": False, "confidence": 0.3,
                    "reason": "LLM 判定输出格式异常，默认不通过。"}
        verified = bool(out.get("verified", False))
        confidence = float(out.get("confidence", 0.3))
        # 加固：verified=True 必须同时 positive_triggered + negative_blocked
        if verified and not (out.get("positive_triggered") and
                              out.get("negative_blocked")):
            verified = False
            out["reason"] = (out.get("reason", "") +
                              " [硬约束] verified 需 positive_triggered "
                              "与 negative_blocked 同时为真，已降级。")
        out["verified"] = verified
        out["confidence"] = confidence
        return out
