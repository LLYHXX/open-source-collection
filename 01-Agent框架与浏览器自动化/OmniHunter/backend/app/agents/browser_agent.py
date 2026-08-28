"""Browser Agent：借鉴 Nanobrowser 的 Planner / Navigator / Validator 三角协作。

用 Playwright 驱动真实浏览器，挖掘命令行工具难覆盖的漏洞：
登录后未授权访问、越权 IDOR、逻辑漏洞、验证码绕过等。

自包含 async 循环：navigate → snapshot → LLM 决策动作 → 执行 → 验证。
Playwright 未安装时优雅降级。
"""
from typing import Any, Callable

from ..config import get_settings
from ..core.base_agent import BaseAgent
from ..core.llm import LLMClient
from ..core.tool_registry import ToolRegistry


class BrowserAgent(BaseAgent):
    role = "browser"
    description = "浏览器自动化挖洞：真实登录态交互，覆盖逻辑漏洞/越权/未授权。"

    def __init__(self, run_id: str, target: Any = None,
                 llm: LLMClient | None = None,
                 tools: ToolRegistry | None = None, memory: Any = None,
                 on_event: Callable[..., None] | None = None):
        super().__init__(run_id, target=target, llm=llm, tools=tools,
                         memory=memory, on_event=on_event)

    async def run(self, task_input: dict) -> dict:
        vuln_types = task_input.get("vuln_types", "")
        url = self.target.url
        settings = get_settings()
        if not settings.browser_enabled:
            self.think("浏览器自动化未启用")
            return {"vulns": []}
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            self.think("playwright 未安装，跳过浏览器挖洞（pip install playwright && playwright install chromium）")
            return {"vulns": []}

        vulns: list[dict] = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.browser_headless)
                page = await browser.new_page()
                await self._navigate(page, url)
                for step in range(8):
                    snapshot = await self._snapshot(page)
                    self.think(f"[step {step}] 页面快照(截断):\n{snapshot[:1200]}")
                    action = self._decide(url, snapshot, vuln_types, step)
                    if not action or action.get("action") == "done":
                        break
                    finding = await self._apply(page, action)
                    if finding:
                        vulns.append(finding)
                await browser.close()
        except Exception as e:  # noqa: BLE001
            self.think(f"浏览器异常: {e}")
        return {"vulns": vulns}

    async def _navigate(self, page, url: str) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:  # noqa: BLE001
            self.think(f"导航失败: {e}")

    async def _snapshot(self, page) -> str:
        try:
            title = await page.title()
            html = await page.content()
            return f"title: {title}\nlen: {len(html)}\n{html[:2000]}"
        except Exception as e:  # noqa: BLE001
            return f"快照失败: {e}"

    def _decide(self, url, snapshot, vuln_types, step) -> dict:
        prompt = (
            f"你是浏览器挖洞决策器。目标: {url}\n关注: {vuln_types}\n第{step}步。\n"
            f"页面快照:\n{snapshot}\n"
            f"选择下一步动作，输出 JSON: {{\"action\":"
            f"\"navigate\"/\"click\"/\"type\"/\"done\", "
            f"\"selector\": \"CSS\", \"text\": \"输入文本\", "
            f"\"reason\": \"\", \"finding\": {{...}} 或 null}}。"
            f"发现漏洞时填 finding(vuln_type/severity/title/detail/evidence/confidence)。"
            f"只输出 JSON。"
        )
        out = self.llm.chat_json([
            {"role": "system", "content": "你只输出 JSON。"},
            {"role": "user", "content": prompt},
        ])
        return out if isinstance(out, dict) else {}

    async def _apply(self, page, action: dict) -> dict | None:
        act = action.get("action")
        sel = action.get("selector")
        try:
            if act == "navigate" and action.get("url"):
                await page.goto(action["url"], timeout=20000)
            elif act == "click" and sel:
                await page.click(sel, timeout=10000)
            elif act == "type" and sel:
                await page.fill(sel, action.get("text", ""), timeout=10000)
        except Exception as e:  # noqa: BLE001
            self.think(f"动作 {act} 失败: {e}")
        return action.get("finding")
