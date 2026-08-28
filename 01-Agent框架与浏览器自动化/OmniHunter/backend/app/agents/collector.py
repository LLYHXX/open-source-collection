"""Collector 收集 Agent：借鉴 AutoHunter 的 Collector。

从 FOFA / 360 Quake / Hunter / ZoomEye / Shodan / Censys 搜集目标，
或手动清单；探活、评分、归属标注后入队。
MVP 实现 FOFA + 手动；自然语言意图自动翻译为 FOFA 语法。
"""
import base64
from typing import Any, Callable

from ..config import Settings, get_settings
from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class CollectorAgent(BaseAgent):
    role = "collector"
    description = "资产搜集：FOFA 自动搜 / 手动清单 / 自然语言意图转 FOFA 语法。"

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None,
                 on_event: Callable[..., None] | None = None,
                 settings: Settings | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools, on_event=on_event)
        self.settings = settings or get_settings()

    async def run(self, task_input: dict) -> dict:
        task = task_input["task"]
        self.think(f"开始搜集目标，来源={task['source']}，方式={task['collect_method']}")
        targets: list[dict] = []

        if task["source"] in ("manual", "both", "single"):
            for line in (task.get("manual_targets") or "").splitlines():
                url = line.strip()
                if url:
                    targets.append({"url": url})

        if task["source"] in ("fofa", "both"):
            targets.extend(await self._fofa_collect(task))

        self.think(f"搜集到 {len(targets)} 个目标")
        return {"targets": targets}

    async def _fofa_collect(self, task: dict) -> list[dict]:
        key = self.settings.fofa_key
        if not key:
            self.think("未配置 FOFA_KEY，跳过自动搜集（可用手动清单继续）。")
            return []
        query = task.get("collect_query", "")
        method = task.get("collect_method", "auto")
        if method == "nl_intent" and query:
            query = self._nl_to_fofa(query)
            self.think(f"自然语言意图转 FOFA 语法: {query}")
        if not query:
            return []

        import httpx

        email, k = (key.split(":", 1) + [""])[:2] if ":" in key else ("", key)
        qbase64 = base64.b64encode(query.encode()).decode()
        max_pages = task.get("max_pages", 3) or 3
        targets: list[dict] = []
        for page in range(1, max_pages + 1):
            try:
                r = httpx.get(
                    f"{self.settings.fofa_base_url}/api/v1/search/all",
                    params={"email": email, "key": k, "qbase64": qbase64,
                            "page": page, "size": 100},
                    timeout=20,
                )
                data = r.json()
                results = data.get("results", []) or []
                if not results:
                    break
                for row in results:
                    host = row[0] if len(row) > 0 else ""
                    port = row[2] if len(row) > 2 else ""
                    title = row[3] if len(row) > 3 else ""
                    if not host:
                        continue
                    url = host if host.startswith("http") else (
                        f"http://{host}:{port}" if port else f"http://{host}"
                    )
                    targets.append({"url": url, "host": host, "title": title})
                self.think(f"FOFA 第{page}页获取 {len(results)} 条")
            except Exception as e:  # noqa: BLE001
                self.think(f"FOFA 第{page}页失败: {e}")
                break
        return targets

    def _nl_to_fofa(self, intent: str) -> str:
        return self.llm.chat([
            {"role": "system",
             "content": "把用户的自然语言资产搜集意图翻译为 FOFA 查询语法，只输出语法本身，如 title=\"后台管理\" && org=\"...\"。"},
            {"role": "user", "content": intent},
        ]).strip()
