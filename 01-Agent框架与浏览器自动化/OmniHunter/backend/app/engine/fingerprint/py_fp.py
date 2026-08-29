"""Python 指纹兜底实现：探活 + 组件识别 + 端点发现（确定性规则）。

能力对齐 httpx（-title -tech-detect -status-code -web-server），
指纹规则覆盖常见 webserver/框架/前端库/CMS。
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from ..http_client import get

# 组件指纹规则：(tech名, 匹配方式, 匹配串)
_TECH_RULES: list[tuple[str, str, str]] = [
    # header 类
    ("php", "header", "x-powered-by:php"),
    ("asp.net", "header", "x-powered-by:asp.net"),
    ("express", "header", "x-powered-by:express"),
    ("thinkphp", "header", "x-powered-by:thinkphp"),
    # cookie 类
    ("php", "header", "set-cookie:phpsessid"),
    ("jsp", "header", "set-cookie:jsessionid"),
    ("asp.net", "header", "set-cookie:asp.net_sessionid"),
    ("laravel", "header", "set-cookie:laravel_session"),
    ("django", "header", "set-cookie:csrftoken"),
    ("shiro", "header", "set-cookie:rememberme"),
    # server 头
    ("nginx", "server", "nginx"),
    ("apache", "server", "apache"),
    ("iis", "server", "microsoft-iis"),
    ("tomcat", "server", "tomcat"),
    ("jetty", "server", "jetty"),
    ("openresty", "server", "openresty"),
    ("caddy", "server", "caddy"),
    # body 类（前端库/框架/CMS）
    ("jquery", "body", "jquery"),
    ("vue", "body", "vue"),
    ("react", "body", "react"),
    ("element-plus", "body", "element-plus"),
    ("bootstrap", "body", "bootstrap"),
    ("webpack", "body", "webpack"),
    ("wordpress", "body", "wp-content"),
    ("wordpress", "body", "wp-includes"),
    ("drupal", "body", "drupal"),
    ("joomla", "body", "joomla"),
    ("discuz", "body", "discuz"),
    ("dedecms", "body", "dedecms"),
    ("phpcms", "body", "phpcms"),
    ("spring", "body", "org.springframework"),
    ("struts", "body", "struts"),
    ("elasticsearch", "body", "elasticsearch"),
    ("swagger", "body", "swagger-ui"),
]

# 端点发现字典：常见入口/信息端点
_DISCOVER_PATHS = (
    "/robots.txt", "/sitemap.xml", "/admin/", "/login", "/api",
    "/swagger-ui.html", "/swagger.json", "/actuator", "/.well-known/security.txt",
    "/index.php", "/admin/login", "/api/v1", "/druid/index.html",
)

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


async def python_fingerprint(base_url: str, timeout: int = 20):
    """探活 + 指纹 + 端点发现。目标不可达返回 None。"""
    from ..base import TargetFingerprint

    r = await get(base_url, timeout=timeout, allow_redirects=True)
    if r.status == 0:
        return None

    parsed = urlparse(str(r.url) or base_url)
    headers_lows = {f"{k.lower()}:{v.lower()}" for k, v in r.headers.items()}
    body_low = (r.text or "").lower()
    server = r.header("server", "")

    techs: list[str] = []
    for name, how, needle in _TECH_RULES:
        hit = (
            (how == "header" and any(needle in h for h in headers_lows))
            or (how == "server" and needle in server.lower())
            or (how == "body" and needle in body_low)
        )
        if hit and name not in techs:
            techs.append(name)

    title = ""
    m = _TITLE_RE.search(r.text or "")
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:120]

    # 端点发现：并发探常见路径（存活才收录）
    import asyncio
    paths: list[str] = []
    root = f"{parsed.scheme}://{parsed.netloc}"

    async def _probe(path: str):
        pr = await get(root + path, timeout=8, allow_redirects=False)
        if pr.status in (200, 401, 403):
            return path
        return None

    results = await asyncio.gather(*(_probe(p) for p in _DISCOVER_PATHS),
                                   return_exceptions=True)
    paths = [p for p in results if isinstance(p, str)]

    # 首页 HTML 内链/接口补充
    from ..http_client import extract_links
    for link in extract_links(r.text or "", base_url):
        path = urlparse(link).path
        if path and path != "/" and path not in paths:
            paths.append(path)

    return TargetFingerprint(
        url=str(r.url) or base_url,
        host=parsed.netloc,
        scheme=parsed.scheme,
        port=parsed.port or (443 if parsed.scheme == "https" else 80),
        status=r.status,
        title=title,
        webserver=server.split("/", 1)[0].strip() if server else "",
        techs=techs,
        paths=paths[:40],
    )
