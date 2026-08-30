"""引擎统一异步 HTTP 客户端 —— 每个请求必须有超时，异常全兜底。

对齐 attacker.py / verifier.py 的 httpx 风格（verify=False + timeout），
统一 UA / 隐蔽头 / 响应封装，插件层不再裸写 httpx。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse


@dataclass
class Response:
    """统一响应封装。status==0 表示请求异常（网络错误/超时）。"""
    status: int = 0
    headers: dict = field(default_factory=dict)
    text: str = ""
    content: bytes = b""
    elapsed: float = 0.0
    error: str = ""
    url: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def header(self, name: str, default: str = "") -> str:
        """大小写不敏感地读取响应头（底层 dict 为普通 dict，键保留原始大小写，
        如 httpx 透传为 Location、Server、Content-Type 等首字母大写形式，
        必须真正按小写归一化比较，不能只 fallback name.lower() 本身）。"""
        target = name.lower()
        for k, v in self.headers.items():
            if k.lower() == target:
                return v if isinstance(v, str) else default
        return default


_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def base_headers(url: str, extra: dict | None = None) -> dict:
    origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    return {
        "User-Agent": _UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": origin,
        **(extra or {}),
    }


async def http_request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    data: str | bytes | None = None,
    json_body: dict | None = None,
    cookies: dict | None = None,
    timeout: float = 10.0,
    allow_redirects: bool = True,
) -> Response:
    """统一请求入口：永不抛异常，失败返回 status=0 的 Response。"""
    try:
        import httpx
    except ImportError:
        return Response(error="httpx 未安装", url=url)
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            verify=False,  # nosec B501 —— 扫描器需接受自签证书
            timeout=timeout,
            follow_redirects=allow_redirects,
        ) as client:
            r = await client.request(
                method.upper(), url, headers=base_headers(url, headers),
                params=params, data=data, json=json_body, cookies=cookies,
            )
            elapsed = time.monotonic() - start
            return Response(
                status=r.status_code,
                headers={k: v for k, v in r.headers.items()},
                text=r.text if len(r.content) < 512 * 1024 else "",
                content=r.content[:1024 * 1024],
                elapsed=elapsed, url=str(r.url),
            )
    except Exception as e:  # noqa: BLE001 —— 兜底一切网络异常
        return Response(error=str(e), elapsed=time.monotonic() - start, url=url)


async def get(url: str, **kw) -> Response:
    return await http_request("GET", url, **kw)


async def post(url: str, **kw) -> Response:
    return await http_request("POST", url, **kw)


def join_url(base: str, path: str) -> str:
    return urljoin(base.rstrip("/") + "/", path.lstrip("/") if not path.startswith("/") else path)


# ===== 页面参数/端点发现（插件共用）=====

_ID_PARAM_NAMES = (
    "id", "uid", "user_id", "userid", "order_id", "orderid", "goods_id",
    "product_id", "doc_id", "file_id", "member_id", "account_id", "cid", "pid",
)


def extract_links(html: str, base: str) -> list[str]:
    """从 HTML 提取同域链接与接口路径（确定性正则，不引第三方解析器）。"""
    import re
    links: list[str] = []
    host = urlparse(base).netloc
    for m in re.finditer(
            r'''(?:href|src|action)\s*=\s*["']([^"']+)["']''', html or ""):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "javascript:", "mailto:", "data:")):
            continue
        full = urljoin(base, raw)
        p = urlparse(full)
        if p.netloc and p.netloc != host:
            continue
        if p.scheme in ("http", "https"):
            links.append(full.split("#", 1)[0])
    # 接口路径：JS 内出现的相对 api 路径
    for m in re.finditer(r'''["'](/(?:api|v\d|user|admin|manage)[\w/\-.]*)["']''',
                         html or ""):
        full = urljoin(base, m.group(1))
        if urlparse(full).netloc == host:
            links.append(full)
    seen: set[str] = set()
    out: list[str] = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:60]


def extract_query_params(url: str) -> dict[str, str]:
    """提取 URL query 参数。"""
    from urllib.parse import parse_qsl
    return dict(parse_qsl(urlparse(url).query, keep_blank_values=True))


def extract_id_params(url: str) -> dict[str, str]:
    """提取 URL 中疑似 ID/编号的参数。"""
    import re
    qs = extract_query_params(url)
    return {
        k: v for k, v in qs.items()
        if k.lower() in _ID_PARAM_NAMES
        or re.fullmatch(r"\d{1,10}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        v or "", re.I)
    }
