"""Code Auditor 白盒代码审计 Agent（区分黑白盒模式的核心环节）。

用户需求：加白盒模式——拿到源码就能扫，不依赖目标运行。

白盒模式（white-box）：
  1) 调 bandit_scan + dlint_scan 静态扫源码目录
  2) LLM 对告警去重 + 误报过滤 + 业务上下文判定真实危害
  3) 输出结构化漏洞清单（含 file/line/severity/payload 修复建议）
  4) 沉淀 code_audit 经验进 Intel(kind="code_audit_profile")

黑盒模式（black-box）：走 run_traffic_pipeline / run_task，不进本 Agent。
"""
import json
from typing import Any, Callable

from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class CodeAuditorAgent(BaseAgent):
    role = "code_auditor"
    description = ("白盒代码审计：Bandit+Dlint 静态扫源码 + LLM 去误报 + 业务判定，"
                   "输出带修复建议的结构化漏洞清单。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        # 白盒模式：target.url 此处表示源码路径（不是 Web URL）
        source_path = task_input.get("source_path") or getattr(
            self.target, "url", "") or ""
        severity = task_input.get("severity", "low")
        self.think(f"白盒代码审计: path={source_path}, severity>={severity}")

        if not source_path:
            return {"vulns": [], "error": "未提供源码路径"}

        # 1) 调白盒工具静态扫
        summary = self.tools.execute("code_audit_summary",
                                      {"target_path": source_path,
                                       "severity": severity})
        self.tool_call("code_audit_summary",
                        {"target_path": source_path}, summary[:800])
        if "未安装" in summary:
            return {"vulns": [], "error": summary}

        # 2) LLM 去误报 + 业务判定 + 结构化
        vulns = self._llm_judge(summary, source_path, task_input)
        self.think(f"白盒审计判定: {len(vulns)} 条真实漏洞（已去误报）")

        # 3) 沉淀 code_audit_profile 进记忆（同源码库下次直接复用）
        if self.memory and vulns:
            self.memory.store("code_audit_profile", source_path,
                              json.dumps({
                                  "vulns": [{"title": v.get("title", ""),
                                             "severity": v.get("severity", ""),
                                             "file": v.get("file", ""),
                                             "line": v.get("line", 0)}
                                            for v in vulns[:30]],
                                  "summary": summary[:2000],
                              }, ensure_ascii=False),
                              confidence=0.8,
                              source=f"code_auditor:{self.target.id}")
            self.think(f"沉淀 code_audit_profile 进记忆 path={source_path}")

        return {"vulns": vulns, "raw_summary": summary}

    def _llm_judge(self, summary: str, source_path: str,
                  task_input: dict) -> list[dict]:
        """LLM 综合判定：去误报 + 业务上下文 + 修复建议。"""
        ctx = task_input.get("business_context", "")
        prompt = (
            f"你是资深白盒代码审计专家。基于 Bandit+Dlint 静态扫描告警，做去误报"
            f"+业务上下文判定+生成修复建议。\n\n"
            f"源码路径: {source_path}\n"
            f"业务上下文: {ctx or '（未提供，按通用 Web 应用判断）'}\n"
            f"原始告警摘要:\n{summary[:3000]}\n\n"
            f"判定准则:\n"
            f"  - 去误报：测试代码/已知安全用法/低危告警可丢弃\n"
            f"  - 严重度校准：结合业务上下文调整（如 SQL 拼接在鉴权代码=high）\n"
            f"  - 必含: title/vuln_type/severity/file/line/detail/payload(修复建议)"
            f"/evidence(原始告警片段)/confidence\n"
            f"输出 JSON 数组，每项: {{\"title\":\"\",\"vuln_type\":\"\","
            f"\"severity\":\"info/low/medium/high/critical\",\"file\":\"\","
            f"\"line\":0,\"detail\":\"\",\"payload\":\"修复建议\",\"evidence\":\"\","
            f"\"confidence\":0-1,\"status\":\"keep\"}}。只输出 JSON 数组。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON 数组。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, list) else []
