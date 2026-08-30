"""资产测绘平台统一查询：FOFA / 360 Quake / Hunter鹰图 / ZoomEye / Shodan / Censys。

每个平台实现 `_search_<name>(query, settings, max_results) -> list[dict]`，
统一输出 [{"url", "host", "title", "platform"}]，查询失败返回空列表不抛异常
（引擎全流程不因单一平台不可用而中断）。

密钥来源 settings：FOFA_KEY / QUAKE_KEY / HUNTER_KEY / ZOOMEYE_KEY / SHODAN_KEY / CENSYS_KEY
（支持动态配置覆盖，键不区分大小写）。
"""
from typing import Any

import httpx

TIMEOUT = 25


def available_platforms(settings) -> dict[str, bool]:
    """各平台密钥是否已配置。"""
    return {
        "fofa": bool(settings.fofa_key),
        "quake": bool(settings.quake_key),
        "hunter": bool(settings.hunter_key),
        "zoomeye": bool(settings.zoomeye_key),
        "shodan": bool(settings.shodan_key),
        "censys": bool(settings.censys_key),
    }


PLATFORM_LABELS = {
    "fofa": "FOFA",
    "quake": "360 Quake",
    "hunter": "Hunter鹰图",
    "zoomeye": "ZoomEye",
    "shodan": "Shodan",
    "censys": "Censys",
}

# 连通性测试默认语句（保证各平台语法合法且有结果）
DEFAULT_TEST_QUERY = {
    "fofa": 'title="test"',
    "quake": 'response:"nginx"',
    "hunter": 'web.title="test"',
    "zoomeye": "site:.com",
    "shodan": "port:443",
    "censys": "services.service_name: HTTP",
}


def search_platform(platform: str, query: str, settings,
                    max_results: int = 100) -> tuple[list[dict], str]:
    """查询单个平台。返回 (items, error)；error 为空表示成功。"""
    handlers = {
        "fofa": _search_fofa,
        "quake": _search_quake,
        "hunter": _search_hunter,
        "zoomeye": _search_zoomeye,
        "shodan": _search_shodan,
        "censys": _search_censys,
    }
    fn = handlers.get((platform or "").lower())
    if not fn:
        return [], f"未知平台: {platform}"
    if not query.strip():
        return [], "查询语法为空"
    try:
        return fn(query.strip(), settings, max_results), ""
    except Exception as e:  # noqa: BLE001
        return [], f"{PLATFORM_LABELS.get(platform, platform)} 查询失败: {e}"


def search_multi(platforms: list[str], query: str, settings,
                 max_results: int = 100) -> dict[str, Any]:
    """并发查询多平台。返回 {"items": [...], "errors": {platform: msg}}。"""
    from concurrent.futures import ThreadPoolExecutor

    items: list[dict] = []
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=len(platforms) or 1) as pool:
        futures = {p: pool.submit(search_platform, p, query, settings, max_results)
                   for p in platforms}
        for p, fut in futures.items():
            try:
                result, err = fut.result()
            except Exception as e:  # noqa: BLE001
                result, err = [], str(e)
            items.extend(result)
            if err:
                errors[p] = err
    return {"items": items, "errors": errors}


# ===== 输出工具 =====

def _mk_url(host: str, port: Any) -> str:
    host = (host or "").strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host
    try:
        port_i = int(port)
    except (TypeError, ValueError):
        port_i = 0
    scheme = "https" if port_i == 443 else "http"
    if port_i and port_i not in (80, 443):
        return f"{scheme}://{host}:{port_i}"
    return f"{scheme}://{host}"


def _item(host: str, port: Any, title: str, platform: str) -> dict | None:
    host = (host or "").strip()
    if not host:
        return None
    return {"url": _mk_url(host, port), "host": host,
            "title": title or "", "platform": platform}


# ===== 各平台实现 =====

def _search_fofa(query: str, settings, max_results: int) -> list[dict]:
    """FOFA：GET /api/v1/search/all，key 支持 email:key 或纯 key。"""
    key = settings.fofa_key
    email, k = (key.split(":", 1) + [""])[:2] if ":" in key else ("", key)
    qbase64 = __import__("base64").b64encode(query.encode()).decode()
    size = min(max_results, 5000)
    items: list[dict] = []
    page = 1
    while len(items) < size:
        r = httpx.get(
            f"{(settings.fofa_base_url or 'https://fofa.info').rstrip('/')}"
            f"/api/v1/search/all",
            params={"email": email, "key": k, "qbase64": qbase64,
                    "page": page, "size": 100},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(f"FOFA API: {data.get('errmsg') or data.get('error')}")
        results = data.get("results", []) or []
        for row in results:
            host = row[0] if len(row) > 0 else ""
            port = row[2] if len(row) > 2 else ""
            title = row[3] if len(row) > 3 else ""
            it = _item(host, port, title, "fofa")
            if it:
                items.append(it)
        if not results or page >= 10:
            break
        page += 1
    return items[:size]


def _search_hunter(query: str, settings, max_results: int) -> list[dict]:
    """Hunter鹰图：GET /openApi/search，search 为 base64(query)。"""
    import base64

    r = httpx.get(
        "https://hunter.qianxin.com/openApi/search",
        params={
            "api-key": settings.hunter_key,
            "search": base64.b64encode(query.encode()).decode(),
            "page": 1,
            "page_size": min(max_results, 100),
            "is_web": 3,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") not in (0, 200, "0", "200"):
        raise RuntimeError(f"Hunter API: {data.get('message')}")
    items: list[dict] = []
    for row in (data.get("data") or {}).get("arr", []) or []:
        it = _item(row.get("url") or row.get("domain") or row.get("ip", ""),
                   row.get("port"), row.get("web_title", ""), "hunter")
        if it:
            items.append(it)
    return items[:max_results]


def _search_quake(query: str, settings, max_results: int) -> list[dict]:
    """360 Quake：POST /api/v3/search/quake_service，header X-QuakeToken。"""
    r = httpx.post(
        "https://quake.360.net/api/v3/search/quake_service",
        headers={"X-QuakeToken": settings.quake_key},
        json={"query": query, "start": 0, "size": min(max_results, 500)},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") not in (0, -1) or not data.get("data"):
        msg = data.get("message") or data.get("code")
        if data.get("code") != 0:
            raise RuntimeError(f"Quake API: {msg}")
    items: list[dict] = []
    for row in data.get("data") or []:
        svc = row.get("service") or {}
        http_svc = svc.get("http") or {}
        hostname = row.get("hostname") or ""
        host = hostname or row.get("ip", "")
        it = _item(host, row.get("port"),
                   http_svc.get("title") or svc.get("name", ""), "quake")
        if it:
            items.append(it)
    return items[:max_results]


def _search_zoomeye(query: str, settings, max_results: int) -> list[dict]:
    """ZoomEye：GET /host/search，header API-KEY。"""
    r = httpx.get(
        "https://api.zoomeye.hk/host/search",
        headers={"API-KEY": settings.zoomeye_key},
        params={"query": query, "page": 1},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    items: list[dict] = []
    for row in data.get("matches", []) or []:
        port_info = row.get("portinfo") or {}
        title = row.get("title") or ""
        if not title:
            web = row.get("webinfo") or {}
            title = web.get("title", "")
        it = _item(row.get("ip", ""), port_info.get("port"), title, "zoomeye")
        if it:
            items.append(it)
    return items[:max_results]


def _search_shodan(query: str, settings, max_results: int) -> list[dict]:
    """Shodan：GET /shodan/host/search。"""
    r = httpx.get(
        "https://api.shodan.io/shodan/host/search",
        params={"key": settings.shodan_key, "query": query, "page": 1},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"Shodan API: {data.get('error')}")
    items: list[dict] = []
    for row in data.get("matches", []) or []:
        host = row.get("ip_str") or (row.get("hostnames") or [""])[0]
        title = (row.get("http") or {}).get("title") or row.get("product", "")
        it = _item(host, row.get("port"), title, "shodan")
        if it:
            items.append(it)
    return items[:max_results]


def _search_censys(query: str, settings, max_results: int) -> list[dict]:
    """Censys：POST /api/v2/hosts/search，key 格式 API_ID:API_SECRET。"""
    api_id, secret = (settings.censys_key.split(":", 1) + [""])[:2] \
        if ":" in settings.censys_key else (settings.censys_key, "")
    r = httpx.post(
        "https://search.censys.io/api/v2/hosts/search",
        auth=(api_id, secret),
        json={"q": query, "per_page": min(max_results, 100)},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"Censys API: {data.get('errors')}")
    items: list[dict] = []
    for row in ((data.get("result") or {}).get("hits")) or []:
        ports = [s.get("port") for s in row.get("services", []) if s.get("port")]
        title = (row.get("dns") or {}).get("names", [""])
        it = _item(row.get("ip", ""), ports[0] if ports else "",
                   title[0] if title else "", "censys")
        if it:
            items.append(it)
    return items[:max_results]


# ===== CVE affected → 各平台查询语句 =====
def build_cve_queries(cve_entry: dict) -> dict[str, str]:
    """把 CVE affected 转成各资产平台的查询语句。

    输入：cve_entry 是 CveEntry 的 dict 形式（含 affected 字段）。
    affected 结构：{"vendor": "...", "product": "...",
                   "versions": [...], "cpe": [...]}。
    策略：
      - 优先 product 关键字 + banner 正则匹配（找到该产品的未修复资产）
      - NVD/OSV 的 affected.product 在 FOFA 用 body/title 匹配 banner，
        Shodan 按 product + version 关键字搜
      - 失败兜底用 cve_id 直接搜（部分平台支持）
    输出：{"fofa": query, "shodan": query, ...}（仅含已能生成的平台）
    """
    affected = cve_entry.get("affected") or {}
    product = (affected.get("product") or "").strip()
    vendor = (affected.get("vendor") or "").strip()
    versions = affected.get("versions") or []
    cve_id = cve_entry.get("cve_id", "")
    queries: dict[str, str] = {}

    # 没产品信息：只能按 CVE-ID 在 Shodan/Quake 的 cve 字段搜
    if not product:
        if cve_id:
            queries["shodan"] = f"vuln:{cve_id}"
            queries["quake"] = f'cve:"{cve_id}"'
        return queries

    # 有产品信息：构造各平台语法
    # FOFA：title/body/banner 包含产品名
    queries["fofa"] = f'title="{product}" || body="{product}"'
    # Shodan：product + 旧版本关键字
    if versions:
        # 取第一个版本作为参考（OSV 里是 >=X <Y 形式，提取 X）
        ver_sample = versions[0].lstrip(">=<")
        if ver_sample and ver_sample != "*":
            queries["shodan"] = f'product:"{product}" version:"{ver_sample}"'
        else:
            queries["shodan"] = f'product:"{product}"'
    else:
        queries["shodan"] = f'product:"{product}"'
    # 加 CVE 兜底
    if cve_id:
        queries["shodan"] = f'({queries["shodan"]}) || vuln:{cve_id}'
    # Quake
    queries["quake"] = f'response:"{product}"'
    if cve_id:
        queries["quake"] = f'({queries["quake"]}) || cve:"{cve_id}"'
    # Hunter
    queries["hunter"] = f'web.body="{product}"'
    # ZoomEye
    queries["zoomeye"] = f'site:{product.lower()}.com'
    # Censys
    queries["censys"] = f'services.service_name: HTTP and services.http.response.html_title: "{product}"'

    return queries


def search_by_cve(cve_entry: dict, settings, platforms: list[str] | None = None,
                  max_results: int = 100) -> dict:
    """按 CVE 搜未修复资产：affected → 各平台查询语句 → 并发查询。

    返回：{"items": [...], "queries": {...}, "errors": {...}}
    items 每条附带 cve_id / query / platform 字段，便于入库 CveAssetHit。
    """
    queries = build_cve_queries(cve_entry)
    if not queries:
        return {"items": [], "queries": {}, "errors": {"_": "CVE 无 affected 信息无法生成查询"}}

    avail = available_platforms(settings)
    # 过滤要查询的平台：显式指定 > 已配置的全部
    if platforms:
        targets = [p for p in platforms if avail.get(p) and p in queries]
    else:
        targets = [p for p, ok in avail.items() if ok and p in queries]

    if not targets:
        return {"items": [], "queries": queries,
                "errors": {"_": "无已配置的平台可查询（请先配置 FOFA/Shodan 等 API Key）"}}

    cve_id = cve_entry.get("cve_id", "")
    all_items: list[dict] = []
    errors: dict[str, str] = {}
    for p in targets:
        q = queries.get(p, "")
        if not q:
            continue
        try:
            items, err = search_platform(p, q, settings, max_results=max_results)
            if err:
                errors[p] = err
                continue
            # 标记来源
            for it in items:
                it["cve_id"] = cve_id
                it["query"] = q
                it["platform"] = p
            all_items.extend(items)
        except Exception as e:  # noqa: BLE001
            errors[p] = str(e)

    # 去重（按 host+port）
    seen: set[str] = set()
    dedup: list[dict] = []
    for it in all_items:
        key = f"{it.get('host', '')}:{it.get('port', 0)}"
        if key in seen:
            continue
        seen.add(key)
        dedup.append(it)

    return {"items": dedup, "queries": queries, "errors": errors}
