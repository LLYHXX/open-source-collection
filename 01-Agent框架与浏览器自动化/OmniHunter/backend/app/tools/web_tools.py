"""Firecrawl 网页抓取/搜索工具（02 爬虫武器）。

Firecrawl 提供 HTTP API：/v2/scrape 把 URL 转 LLM-ready markdown，
/v2/search 按关键词搜索并返回结构化结果。

未配置 API key 时返回友好提示，便于无 key 环境跑通流程。
"""
from ..config import get_settings


def _client_headers(api_key: str | None) -> dict:
    key = api_key or get_settings().fofa_key or ""  # 复用现有 key 字段占位
    # 优先用环境变量 FIRECRAWL_API_KEY
    import os
    key = api_key or os.getenv("FIRECRAWL_API_KEY", "") or key
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"} if key else {}


def web_scrape(url: str, api_key: str | None = None, timeout: int = 60) -> str:
    """抓取单个 URL，返回 LLM 友好的 markdown。"""
    try:
        import httpx
    except ImportError:
        return "httpx 未安装（pip install httpx），无法调用 Firecrawl。"
    headers = _client_headers(api_key)
    if not headers:
        return ("Firecrawl 未配置 API key。请在环境变量设置 FIRECRAWL_API_KEY，"
                "或访问 https://www.firecrawl.dev/ 获取 key。")
    try:
        r = httpx.post(
            "https://api.firecrawl.dev/v2/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers=headers,
            timeout=timeout,
        )
        if r.status_code >= 400:
            return f"Firecrawl 错误 {r.status_code}: {r.text[:500]}"
        data = r.json()
        return data.get("data", {}).get("markdown") or str(data)[:2000]
    except Exception as e:  # noqa: BLE001
        return f"Firecrawl 抓取失败: {e}"


def web_search(query: str, limit: int = 5, api_key: str | None = None,
               timeout: int = 60) -> str:
    """按关键词搜索网页，返回结构化结果。"""
    try:
        import httpx
    except ImportError:
        return "httpx 未安装（pip install httpx），无法调用 Firecrawl。"
    headers = _client_headers(api_key)
    if not headers:
        return ("Firecrawl 未配置 API key。请在环境变量设置 FIRECRAWL_API_KEY，"
                "或访问 https://www.firecrawl.dev/ 获取 key。")
    try:
        r = httpx.post(
            "https://api.firecrawl.dev/v2/search",
            json={"query": query, "limit": limit},
            headers=headers,
            timeout=timeout,
        )
        if r.status_code >= 400:
            return f"Firecrawl 错误 {r.status_code}: {r.text[:500]}"
        import json
        data = r.json()
        results = data.get("data", data)
        if not isinstance(results, list):
            return json.dumps(data, ensure_ascii=False)[:2000]
        lines = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "")
            link = item.get("url", "")
            lines.append(f"{i}. {title}\n   {link}")
        return "\n".join(lines) or "Firecrawl 搜索无结果"
    except Exception as e:  # noqa: BLE001
        return f"Firecrawl 搜索失败: {e}"
