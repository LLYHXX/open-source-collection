"""Collector 收集 Agent：借鉴 AutoHunter 的 Collector。

从 FOFA / 360 Quake / Hunter / ZoomEye / Shodan / Censys 搜集目标，
或手动清单；探活、评分、归属标注后入队。
支持多平台并发查询（source=all），自然语言意图自动翻译为对应平台语法。
"""
import asyncio
from typing import Any, Callable

from ..config import Settings, get_settings
from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry
from ..tools import asset_platforms

PLATFORM_SOURCES = {"fofa", "quake", "hunter", "zoomeye", "shodan", "censys",
                    "all", "both"}

_NL_SYNTAX_HINTS = {
    "fofa": 'FOFA 语法，如 title="后台管理" && org="..."',
    "hunter": 'Hunter鹰图语法，如 web.title="后台管理"',
    "quake": '360 Quake 语法，如 title:"后台管理"',
    "zoomeye": 'ZoomEye 语法，如 title:"后台管理"',
    "shodan": 'Shodan 语法，如 title:"admin" hostname:"edu.cn"',
    "censys": 'Censys 语法，如 services.http.response.html_title:"后台"',
}


class CollectorAgent(BaseAgent):
    role = "collector"
    description = ("资产搜集：FOFA/Quake/Hunter/ZoomEye/Shodan/Censys 自动搜 / "
                   "手动清单 / 自然语言意图转平台语法。")

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None,
                 memory: Any = None,
                 on_event: Callable[..., None] | None = None,
                 router: Any = None,
                 pruning: Any = None,
                 settings: Settings | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools, memory=memory,
                         on_event=on_event, router=router, pruning=pruning)
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

        if task["source"] in PLATFORM_SOURCES:
            targets.extend(await self._platform_collect(task))

        self.think(f"搜集到 {len(targets)} 个目标")
        return {"targets": targets}

    def _resolve_platforms(self, source: str) -> list[str]:
        """source -> 平台列表（仅保留已配置密钥的平台）。"""
        avail = asset_platforms.available_platforms(self.settings)
        if source == "all":
            return [p for p, ok in avail.items() if ok]
        if source == "both":
            return ["fofa"] if avail.get("fofa") else []
        if source in PLATFORM_SOURCES:
            return [source] if avail.get(source) else []
        return []

    async def _platform_collect(self, task: dict) -> list[dict]:
        """多平台并发搜集（同步 API 调用放到线程，不阻塞事件循环）。"""
        platforms = self._resolve_platforms(task["source"])
        if not platforms:
            self.think("未配置任何资产平台密钥，跳过自动搜集（可用手动清单继续）。")
            return []

        query = (task.get("collect_query") or "").strip()
        method = task.get("collect_method", "auto")
        if method == "nl_intent" and query:
            # all 模式以 FOFA 语法为基准（各平台翻译损耗大，保持确定性）
            target_for_nl = "fofa" if len(platforms) > 1 else platforms[0]
            translated = await self._nl_to_query(query, target_for_nl)
            if translated:
                query = translated
            self.think(f"自然语言意图转 {target_for_nl.upper()} 语法: {query}")
        if not query:
            self.think("查询语法为空，跳过平台搜集。")
            return []

        self.think(f"平台 {','.join(platforms)} 并发查询: {query}")
        result = await asyncio.to_thread(
            asset_platforms.search_multi, platforms, query, self.settings,
            max_results=100 * (task.get("max_pages", 3) or 3),
        )
        for p, err in (result.get("errors") or {}).items():
            self.think(f"{asset_platforms.PLATFORM_LABELS.get(p, p)}: {err}")
        items = result.get("items", [])
        by_platform: dict[str, int] = {}
        for it in items:
            by_platform[it.get("platform", "?")] = \
                by_platform.get(it.get("platform", "?"), 0) + 1
        self.think("平台获取统计: " + (", ".join(f"{k}={v}" for k, v in
                                                by_platform.items()) or "0 条"))
        return items

    async def _nl_to_query(self, intent: str, platform: str) -> str:
        if not self.llm:
            return intent  # 无 LLM 时原样使用（用户可直接填平台语法）
        hint = _NL_SYNTAX_HINTS.get(platform, _NL_SYNTAX_HINTS["fofa"])
        return (await self.llm.achat([
            {"role": "system",
             "content": f"把用户的自然语言资产搜集意图翻译为{hint}。"
                        "只输出语法本身，不要解释。"},
            {"role": "user", "content": intent},
        ])).strip()
