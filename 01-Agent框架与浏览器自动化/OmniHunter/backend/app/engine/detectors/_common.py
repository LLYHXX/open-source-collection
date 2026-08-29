"""检测插件公共助手：注入点发现（表单解析 + 常见参数字典）。"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from ..base import ScanContext
from ..http_client import get

# 常见可注入参数字典（确定性，覆盖多数站点的搜索/列表/详情参数）
COMMON_PARAMS = (
    "q", "s", "search", "keyword", "kw", "wd", "query", "name", "title",
    "id", "uid", "pid", "cid", "gid", "cat", "cate", "category", "type",
    "page", "sort", "order", "orderby", "filter", "tag", "keywords",
    "year", "month", "date", "status", "lang", "file", "path", "url",
)

_FORM_RE = re.compile(
    r"<form[^>]*action\s*=\s*[\"']([^\"']*)[\"'][^>]*>(.*?)</form>",
    re.I | re.S)
_INPUT_RE = re.compile(
    r"<input[^>]*name\s*=\s*[\"']([^\"']+)[\"']", re.I)
_SELECT_RE = re.compile(
    r"<select[^>]*name\s*=\s*[\"']([^\"']+)[\"']", re.I)


async def discover_inject_points(ctx: ScanContext) -> list[dict]:
    """发现注入点：[{url, params: [name,...], method}]。

    来源：首页/代表页 form 解析 + URL 参数 + 常见参数字典探测。
    """
    points: list[dict] = []
    seen: set[tuple] = set()

    # 1) 指纹层发现的路径 + 首页
    probe_urls = [ctx.base_url]
    root = f"{urlparse(ctx.base_url).scheme}://{urlparse(ctx.base_url).netloc}"
    for p in ctx.fp.paths[:10]:
        if not re.search(r"\.(js|css|png|jpg|jpeg|gif|ico|svg)$", p, re.I):
            probe_urls.append(urljoin(root, p))

    for u in probe_urls:
        r = await get(u, timeout=8)
        html = r.text or ""
        # 2) form 解析
        for fm in _FORM_RE.finditer(html):
            action = fm.group(1) or u
            action_url = urljoin(u, action)
            names = [n for n in _INPUT_RE.findall(fm.group(2))
                     if n.lower() not in ("submit", "token", "csrf")]
            names += _SELECT_RE.findall(fm.group(2))
            if names:
                key = (action_url, tuple(names[:8]))
                if key not in seen:
                    seen.add(key)
                    points.append({"url": action_url, "params": names[:8],
                                   "method": "GET"})
        # 3) URL 自带参数
        if urlparse(u).query:
            from urllib.parse import parse_qsl
            names = [k for k, _ in parse_qsl(urlparse(u).query)]
            key = (u, tuple(names[:8]))
            if key not in seen:
                seen.add(key)
                points.append({"url": u, "params": names[:8], "method": "GET"})

    # 4) 常见参数字典兜底（对首页 GET）
    key = (ctx.base_url, tuple(COMMON_PARAMS[:8]))
    if key not in seen:
        seen.add(key)
        points.append({"url": ctx.base_url, "params": list(COMMON_PARAMS)[:8],
                       "method": "GET"})

    return points[:15]
