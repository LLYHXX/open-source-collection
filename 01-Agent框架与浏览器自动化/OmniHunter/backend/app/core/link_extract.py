"""Link-Extend Hook：从 Intel value 中抽取候选链写入 MinerCandidate。

三规则（纯正则，零 HTTP 调用，不触发任何外部网络）：
  1) hostname：(?<![\\w.-])([a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)+)
     例：example.com / sub.example.org / api-v2.stg.internal
  2) IPv4 字面量：25[0-5] / 2[0-4]\\d / [01]?\\d\\d（点分四段）
  3) CVE ID：(?i)CVE-\\d{4}-\\d{4,7}

Scope 语义（来自 MinerConfig.scope_asset_ids）：
  - 空 scope：视为未启用授权范围，**跳过 MinerCandidate 写入**，避免
    未经用户明确授权先入库。
  - 非空 scope：对 host/IP 结果，命中 scope 任一匹配 → MinerCandidate.pending；
    不命中 → status=skipped, note=out_of_scope。对 CVE：一律视为
    越权无关信息（scope 是资产域不是 CVE 域），直接 pending 不做 scope 限制。

本模块不写任何 Setting，只依赖调用方传入 scope_asset_ids。
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Intel, MinerCandidate

# ===== Regex =====
_HOSTNAME_RE = re.compile(
    r"(?<![\w.-])([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+){1,})(?![\w.-])"
)
_IPV4_RE = re.compile(
    r"(?<![\d.])"
    r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
    r"(?![\d.])"
)
_CVE_RE = re.compile(r"(?i)(?<![A-Z0-9-])(CVE-\d{4}-\d{4,7})(?![A-Z0-9-])")


@dataclass
class ExtractedHit:
    kind: str          # "hostname" | "ipv4" | "cve_id"
    key: str           # 规范化后的抽取值（host/ip/cve-id upper）
    snippet: str = ""  # 命中的原文片段（用于 note 溯源，可选）


def _extract_all(text: str) -> list[ExtractedHit]:
    """从文本中抽取三类命中，去重并做基本规范化。"""
    hits: list[ExtractedHit] = []
    seen: set[tuple[str, str]] = set()
    if not text:
        return hits

    # hostname
    for m in _HOSTNAME_RE.finditer(text):
        host = m.group(1).rstrip(".").lower()
        # 过滤明显非域名：无 "."（理论不会，因为 regex 要求两段+）或单段
        if "." not in host:
            continue
        key = ("hostname", host)
        if key in seen:
            continue
        seen.add(key)
        hits.append(ExtractedHit(kind="hostname", key=host, snippet=m.group(0)))

    # IPv4
    for m in _IPV4_RE.finditer(text):
        raw = m.group(0)
        try:
            ip = ipaddress.IPv4Address(raw)
        except ValueError:
            continue
        # 去掉明显广播类：0.0.0.0 / 255.255.255.255 保留命中（它们可能是情报）
        key = ("ipv4", str(ip))
        if key in seen:
            continue
        seen.add(key)
        hits.append(ExtractedHit(kind="ipv4", key=str(ip), snippet=raw))

    # CVE ID：大写规范化
    for m in _CVE_RE.finditer(text):
        cve = m.group(1).upper()
        key = ("cve_id", cve)
        if key in seen:
            continue
        seen.add(key)
        hits.append(ExtractedHit(kind="cve_id", key=cve, snippet=m.group(0)))

    return hits


def _scope_match(kind: str, key: str, scope: list[str]) -> bool:
    """判断命中是否在授权 scope 内。

    scope 每一项支持三类格式（宽松匹配，拒绝任何 DNS/外部调用）：
      - 精确 host: example.com
      - 后缀域: .example.com 匹配 * .example.com
      - CIDR/IP: 192.168.1.0/24 或 10.0.0.5
      - 字符串 "*" 或空：此处不处理，调用方应当在 scope 空时整体跳过。
    """
    if not scope:
        return False
    scope_clean = [s.strip() for s in scope if s and s.strip()]
    if not scope_clean:
        return False

    if kind == "cve_id":
        # CVE 不依赖资产域，一律放行（scope 仅限定 IP/host 资产）
        return True

    if kind == "ipv4":
        try:
            ip = ipaddress.IPv4Address(key)
        except ValueError:
            return False
        for s in scope_clean:
            try:
                if "/" in s:
                    net = ipaddress.IPv4Network(s, strict=False)
                    if ip in net:
                        return True
                else:
                    if str(ipaddress.IPv4Address(s)) == str(ip):
                        return True
            except ValueError:
                continue
        return False

    if kind == "hostname":
        host = key.lower()
        for s in scope_clean:
            sc = s.lower().lstrip()
            if not sc:
                continue
            if sc.startswith("."):
                if host.endswith(sc) or host == sc[1:]:
                    return True
            else:
                if host == sc or host.endswith("." + sc):
                    return True
        return False

    return False


def _canon_kind_to_intel_kind(k: str) -> str:
    """MinerCandidate.extracted_kind → Intel.kind（规范化）。"""
    return {
        "hostname": "hostname",
        "ipv4":     "ipv4",
        "cve_id":   "cve_id",
    }.get(k, k)


def extract_and_persist_candidates(
    db: Session,
    intel_list: list[Intel],
    scope_asset_ids: list[str],
) -> int:
    """从给定 Intel list 的 value 中抽取候选并写入 MinerCandidate。

    Returns: 新增的 status=pending 的 MinerCandidate 数（越权项=skipped 不计数，
    重复项不重复入库：唯一索引 = (src_intel_id, extracted_kind, extracted_key)）。
    """
    if not intel_list:
        return 0
    # scope 空 → **严格不写任何候选**，避免越授权
    if not scope_asset_ids or not any(str(s).strip() for s in scope_asset_ids):
        return 0

    pending_count = 0
    for intel in intel_list:
        if not intel or not intel.id:
            continue
        for hit in _extract_all(intel.value or ""):
            # 幂等：若该来源+kind+key 已经有记录，跳过不重复加
            existing = db.scalar(
                select(MinerCandidate)
                .where(MinerCandidate.src_intel_id == intel.id)
                .where(MinerCandidate.extracted_kind == _canon_kind_to_intel_kind(hit.kind))
                .where(MinerCandidate.extracted_key == hit.key)
            )
            if existing:
                continue
            in_scope = _scope_match(hit.kind, hit.key, scope_asset_ids)
            cand = MinerCandidate(
                src_intel_id=intel.id,
                extracted_kind=_canon_kind_to_intel_kind(hit.kind),
                extracted_key=hit.key,
                status="pending" if in_scope else "skipped",
                note="" if in_scope else "out_of_scope",
            )
            db.add(cand)
            if in_scope:
                pending_count += 1
    db.flush()
    return pending_count


def extract_from_db_intel_ids(
    db: Session,
    intel_ids: list[str],
    scope_asset_ids: list[str],
) -> int:
    """便捷包装：根据 Intel ID 列表抽取候选。"""
    if not intel_ids:
        return 0
    items = db.scalars(select(Intel).where(Intel.id.in_(list(intel_ids)))).all()
    return extract_and_persist_candidates(db, list(items), scope_asset_ids)


if __name__ == "__main__":  # pragma: no cover - 手动 smoke
    s = "Credentials admin@example.com:pass for 10.0.0.1 and ref CVE-2024-12345; sub.stg.example.local"
    print([(h.kind, h.key) for h in _extract_all(s)])
    dbg_db = SessionLocal()
    try:
        pass
    finally:
        dbg_db.close()
