"""idor_traverse —— IDOR 检测确定性模块（方案第二步第 2 点）。

自动识别接口里的 ID/编号参数，遍历邻近枚举值，对比不同 ID 的响应内容，
判断能否越权访问他人数据：
- 提取 query 中的 id 类参数（id/uid/order_id/... 或纯数字/UUID 值）
- 变异为 id±1..±3 / 相邻 UUID 简化值重放
- 响应内容与新 ID 出现 + 内容差异 → 疑似 IDOR
- verify: 二次重放一致才确认
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from ..base import ScanContext, SuspectFinding
from ..http_client import extract_id_params, http_request


def _mutate_value(v: str, delta: int) -> str | None:
    """数值型 id 做 ±delta；UUID 做末段微变。"""
    if re.fullmatch(r"\d{1,10}", v):
        return str(max(1, int(v) + delta))
    m = re.fullmatch(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-)([0-9a-f]{12})",
                     v, re.I)
    if m:
        tail = int(m.group(2)[:4], 16)
        new_tail = f"{(tail + delta) % 0xffff:04x}"
        return m.group(1) + new_tail + m.group(2)[4:]
    return None


def _build_url(url: str, param: str, new_value: str) -> str:
    parsed = urlparse(url)
    qs = [(k, new_value if k == param else v)
          for k, v in parse_qsl(parsed.query, keep_blank_values=True)]
    return urlunparse(parsed._replace(query=urlencode(qs)))


def _body_sig(text: str) -> str:
    return hashlib.md5(text[:8000].encode("utf-8", "ignore")).hexdigest()


async def run_idor_traverse(ctx: ScanContext,
                            findings: list[SuspectFinding]) -> None:
    """对目标 URL 及指纹路径中带 ID 参数的接口做枚举遍历。"""
    urls = [ctx.base_url] + [u for p in ctx.fp.paths
                             if (u := _abs(ctx.base_url, p)) and extract_id_params(u)]
    for url in urls[:20]:
        id_params = extract_id_params(url)
        if not id_params:
            continue
        # 基线：原样请求
        base_r = await http_request("GET", url, timeout=10)
        if base_r.status == 0 or not (200 <= base_r.status < 300):
            continue
        base_sig = _body_sig(base_r.text or "")

        for param, value in id_params.items():
            for delta in (1, -1, 2, 3):
                new_val = _mutate_value(value, delta)
                if not new_val or new_val == value:
                    continue
                probe_url = _build_url(url, param, new_val)
                r = await http_request("GET", probe_url, timeout=10)
                if r.status == 0 or not (200 <= r.status < 300):
                    continue
                body = r.text or ""
                sig = _body_sig(body)
                # 判定：响应与基线不同 + 响应中出现新 ID 值（拿到了他人数据）
                has_new_id = new_val.lower() in body.lower()
                diff_content = sig != base_sig and abs(len(body) - len(base_r.text or "")) > 50
                if has_new_id and diff_content:
                    findings.append(SuspectFinding(
                        plugin_id="idor_traverse",
                        vuln_type="idor",
                        title=(f"疑似 IDOR：{param}={value} 可遍历访问 "
                               f"{param}={new_val} 的数据"),
                        detail=(
                            f"接口 {url} 的 ID 参数 {param} 未做归属校验："
                            f"将 {param} 改为 {new_val} 后仍返回 2xx，"
                            f"且响应内容与基线不同并包含新 ID 值，"
                            f"可水平越权读取他人数据。"
                        ),
                        payload=f"{param}={new_val}",
                        evidence=(f"baseline {base_r.status}/{len(base_r.content)}B; "
                                  f"mutated {r.status}/{len(r.content)}B "
                                  f"(含 {param}={new_val})"),
                        url=probe_url, param=param,
                        vector="AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
                        confidence=0.7,
                    ))
                    break  # 该参数命中一次即够


def _abs(base: str, path: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, path)


async def verify_idor_finding(ctx: ScanContext,
                              finding: SuspectFinding) -> SuspectFinding | None:
    """IDOR 独立复现：等待片刻后二次重放变异请求，结果一致才确认。"""
    import asyncio
    await asyncio.sleep(1.0)
    r = await http_request("GET", finding.url, timeout=10)
    if r.status == 0 or not (200 <= r.status < 300):
        return None
    param, new_val = finding.param, finding.payload.split("=", 1)[-1]
    if (new_val or "").lower() in (r.text or "").lower():
        finding.verified = True
        finding.verify_evidence = (
            f"复现: 二次请求 {param}={new_val} -> {r.status}/{len(r.content)}B，"
            f"响应仍包含越权数据")
        finding.confidence = min(0.9, finding.confidence + 0.15)
        return finding
    return None
