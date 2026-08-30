"""CVE 库拉取与去重入库：NVD 官方 API + OSV.dev 双源融合。

NVD：https://services.nvd.nist.gov/rest/json/cves/2.0
OSV.dev：https://api.osv.dev/v1/query （按时间批量拉取）

策略：
  - 优先 NVD（数据最权威）；NVD 限速 5 req/30min（无 key），有 key 50 req/30min
  - OSV 作为补充（覆盖 GitHub/CycloneDX 生态更全），按 published_at 反查
  - 按 CVE-ID 去重；同一 CVE 已存在则更新 affected/cvss/updated_at_src
  - 全程不抛异常：拉失败返回空列表，错误信息回传 caller

返回：{"added": int, "updated": int, "errors": [...]}
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from ..models import CveEntry

log = logging.getLogger("aififteen-hunter")

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OSV_API = "https://api.osv.dev/v1/query"
TIMEOUT = 30
NVD_MAX_RESULTS_PER_PAGE = 2000


def _parse_dt(s: str | None) -> datetime | None:
    """解析 ISO8601 时间串：兼容 NVD 的 '2024-01-01T00:00:00.000' 与 OSV 的 RFC3339。"""
    if not s:
        return None
    try:
        # 去掉 Z 后缀，统一 naive UTC
        s = s.strip().rstrip("Z")
        if "." in s:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except Exception:  # noqa: BLE001
        return None


def _severity_from_score(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return ""


# ===== NVD =====
async def fetch_nvd_cves(api_key: str, days: int = 7,
                        max_results: int = 500) -> list[dict]:
    """NVD 官方 API：拉取最近 N 天的 CVE。

    使用 pubStartDate 过滤；NVD 单次最多返回 2000 条，
    分页拉取直到达到 max_results 或无更多数据。
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    params = {
        "pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000"),
        "pubEndDate": end.strftime("%Y-%m-%dT00:00:00.000"),
        "resultsPerPage": str(min(2000, max_results)),
    }
    headers = {"apiKey": api_key} if api_key else {}

    items: list[dict] = []
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        start_index = 0
        total = None
        while True:
            params["startIndex"] = str(start_index)
            try:
                r = await client.get(NVD_API, params=params)
                if r.status_code == 403:
                    log.warning("NVD API 限速（403），稍后重试或换 OSV 源")
                    break
                r.raise_for_status()
                data = r.json()
            except Exception as e:  # noqa: BLE001
                log.warning("NVD 拉取失败 (startIndex=%s): %s", start_index, e)
                break

            vulns = data.get("vulnerabilities", []) or []
            for v in vulns:
                cve = v.get("cve", {})
                parsed = _parse_nvd_cve(cve)
                if parsed:
                    items.append(parsed)

            total = data.get("totalResults", 0)
            start_index += len(vulns)
            if start_index >= total or len(items) >= max_results or not vulns:
                break
            # NVD 无 key 限速 5 req/30min：拉完一页 sleep 1s 避免触发限速
            await asyncio.sleep(1.0)
    log.info("NVD 拉取完成：共 %d 条（最近 %d 天）", len(items), days)
    return items[:max_results]


def _parse_nvd_cve(cve: dict) -> dict | None:
    """NVD 单条 CVE 标准化为统一结构。"""
    cve_id = cve.get("id", "")
    if not cve_id:
        return None

    descs = cve.get("descriptions", []) or []
    desc = ""
    for d in descs:
        if d.get("lang") == "en":
            desc = d.get("value", "")
            break
    if not desc and descs:
        desc = descs[0].get("value", "")

    # affected：从 configurations[].cpeMatch 提取 vendor/product/cpe
    affected: dict[str, Any] = {"vendor": "", "product": "", "versions": [], "cpe": []}
    for conf in cve.get("configurations", []) or []:
        for node in conf.get("nodes", []) or []:
            for m in node.get("cpeMatch", []) or []:
                cpe = m.get("criteria", "")
                if not cpe:
                    continue
                affected["cpe"].append(cpe)
                # cpe:2.3:a:vendor:product:version:...
                parts = cpe.split(":")
                if len(parts) >= 6:
                    if not affected["vendor"]:
                        affected["vendor"] = parts[3]
                    if not affected["product"]:
                        affected["product"] = parts[4]
                    if parts[5] and parts[5] != "*":
                        affected["versions"].append(parts[5])
    affected["versions"] = list(set(affected["versions"]))[:20]  # 去重 + 限长

    # CVSS
    cvss_score = 0.0
    cvss_severity = ""
    cvss_vector = ""
    for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        metrics = cve.get("metrics", {}).get(metric_key, [])
        if metrics:
            m = metrics[0].get("cvssData", {})
            cvss_score = float(m.get("baseScore", 0) or 0)
            cvss_severity = (m.get("baseSeverity") or
                             _severity_from_score(cvss_score))
            cvss_vector = m.get("vectorString", "")
            break

    # references
    refs = [r.get("url", "") for r in cve.get("references", []) or []
            if r.get("url")]
    return {
        "cve_id": cve_id,
        "source": "nvd",
        "title": desc[:120] if desc else cve_id,
        "description": desc,
        "affected": affected,
        "cvss_score": cvss_score,
        "cvss_severity": cvss_severity,
        "cvss_vector": cvss_vector,
        "published_at": _parse_dt(cve.get("published")),
        "updated_at_src": _parse_dt(cve.get("lastModified")),
        "references": refs[:20],
    }


# ===== OSV =====
async def fetch_osv_cves(days: int = 7, max_results: int = 500) -> list[dict]:
    """OSV.dev：按 batch 拉取最近 N 天新增漏洞。

    OSV 没有按时间过滤的官方端点，用 /v1/query 的 package 维度
    不通用；改用 /v1/vuls/{id} 列表 + 已知 eco 列表（PyPI/npm/Go）批量查询。
    简化实现：直接 POST /v1/query 不带参数拉全量最近条目，按时间过滤。
    """
    items: list[dict] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    # OSV 不支持时间过滤，用每个生态批量拉 + 客户端过滤
    ecosystems = ["PyPI", "npm", "Go", "Maven", "OSS-Fuzz"]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for eco in ecosystems:
            try:
                r = await client.post(OSV_API, json={
                    "package": {"ecosystem": eco},
                    "query_format": "list",
                })
                if r.status_code != 200:
                    continue
                data = r.json()
            except Exception as e:  # noqa: BLE001
                log.warning("OSV 拉取失败 (eco=%s): %s", eco, e)
                continue

            for vuln in data.get("vulns", []) or []:
                parsed = _parse_osv_vuln(vuln)
                if not parsed:
                    continue
                published = parsed.get("published_at")
                if published and published < cutoff:
                    continue
                items.append(parsed)
                if len(items) >= max_results:
                    return items[:max_results]
    log.info("OSV 拉取完成：共 %d 条（最近 %d 天，已过滤）", len(items), days)
    return items[:max_results]


def _parse_osv_vuln(v: dict) -> dict | None:
    """OSV vuln 标准化为统一结构。"""
    # OSV id 可能不是 CVE；优先取 aliases 里的 CVE-ID
    vid = v.get("id", "")
    cve_id = ""
    for alias in v.get("aliases", []) or []:
        if alias.startswith("CVE-"):
            cve_id = alias
            break
    if not cve_id:
        # 非 CVE 类漏洞（如 GHSA/PYSEC）也保留，用原 id
        cve_id = vid

    summary = v.get("summary", "") or ""
    details = v.get("details", "") or ""

    # affected：从 affected[].package + ranges 提取
    affected: dict[str, Any] = {"vendor": "", "product": "", "versions": [], "cpe": []}
    for aff in v.get("affected", []) or []:
        pkg = aff.get("package", {}) or {}
        ecosystem = pkg.get("ecosystem", "")
        name = pkg.get("name", "")
        if name and not affected["product"]:
            affected["product"] = name
            affected["vendor"] = ecosystem
        for rng in aff.get("ranges", []) or []:
            for ev in rng.get("events", []) or []:
                introduced = ev.get("introduced")
                fixed = ev.get("fixed")
                if introduced:
                    affected["versions"].append(f">={introduced}")
                if fixed:
                    affected["versions"].append(f"<{fixed}")

    # CVSS：OSV severity 数组
    cvss_score = 0.0
    cvss_severity = ""
    cvss_vector = ""
    for sev in v.get("severity", []) or []:
        if sev.get("type") in ("CVSS_V3", "CVSS_V4"):
            vector = sev.get("score", "")
            cvss_vector = vector
            # 简化：从 vector 字符串里取 base score 不现实，OSV 不直接提供
            # 取 database_specific 里的 severity 作为兜底
            break
    db_specific = v.get("database_specific", {}) or {}
    sev_str = db_specific.get("severity", "")
    if sev_str:
        cvss_severity = sev_str.upper()
        # 简化 score 估算
        score_map = {"LOW": 3.0, "MODERATE": 5.0, "MEDIUM": 6.0,
                     "HIGH": 8.0, "CRITICAL": 9.5}
        cvss_score = score_map.get(cvss_severity, 0.0)
        cvss_severity = "MEDIUM" if cvss_severity == "MODERATE" else cvss_severity

    refs = [r.get("url", "") for r in v.get("references", []) or []
            if r.get("url")]
    return {
        "cve_id": cve_id,
        "source": "osv",
        "title": summary[:120] if summary else cve_id,
        "description": details or summary,
        "affected": affected,
        "cvss_score": cvss_score,
        "cvss_severity": cvss_severity,
        "cvss_vector": cvss_vector,
        "published_at": _parse_dt(v.get("published")),
        "updated_at_src": _parse_dt(v.get("modified")),
        "references": refs[:20],
    }


# ===== 合并入库 =====
def merge_and_save_cves(cves: list[dict], db) -> dict:
    """去重合并入库：以 cve_id 唯一，已存在则更新最新字段。"""
    from sqlalchemy import select

    added = 0
    updated = 0
    errors: list[str] = []
    # 批量查询已存在记录
    cve_ids = [c["cve_id"] for c in cves if c.get("cve_id")]
    existing_map: dict[str, CveEntry] = {}
    if cve_ids:
        # SQLite IN 子句有上限，分批查询
        for i in range(0, len(cve_ids), 500):
            batch = cve_ids[i:i + 500]
            rows = db.scalars(select(CveEntry).where(CveEntry.cve_id.in_(batch))).all()
            for r in rows:
                existing_map[r.cve_id] = r

    for c in cves:
        cve_id = c.get("cve_id", "")
        if not cve_id:
            continue
        try:
            existing = existing_map.get(cve_id)
            if existing:
                # 更新（NVD 优先级高于 OSV，不覆盖 NVD 已有数据）
                if existing.source == "nvd" and c.get("source") == "osv":
                    continue
                existing.title = c.get("title") or existing.title
                existing.description = c.get("description") or existing.description
                if c.get("affected"):
                    existing.affected = c["affected"]
                if c.get("cvss_score", 0) > 0:
                    existing.cvss_score = c["cvss_score"]
                    existing.cvss_severity = c.get("cvss_severity", "")
                    existing.cvss_vector = c.get("cvss_vector", "")
                if c.get("published_at"):
                    existing.published_at = c["published_at"]
                if c.get("updated_at_src"):
                    existing.updated_at_src = c["updated_at_src"]
                if c.get("references"):
                    existing.references = c["references"]
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                entry = CveEntry(
                    cve_id=cve_id,
                    source=c.get("source", "nvd"),
                    title=c.get("title", ""),
                    description=c.get("description", ""),
                    affected=c.get("affected", {}) or {},
                    cvss_score=c.get("cvss_score", 0.0),
                    cvss_severity=c.get("cvss_severity", ""),
                    cvss_vector=c.get("cvss_vector", ""),
                    published_at=c.get("published_at"),
                    updated_at_src=c.get("updated_at_src"),
                    references=c.get("references", []) or [],
                )
                db.add(entry)
                existing_map[cve_id] = entry
                added += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{cve_id}: {e}")
            continue

    try:
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        errors.append(f"commit failed: {e}")
        return {"added": 0, "updated": 0, "errors": errors}

    log.info("CVE 库入库完成：新增 %d，更新 %d，错误 %d", added, updated, len(errors))
    return {"added": added, "updated": updated, "errors": errors}


async def fetch_and_update_cves(settings, db, days: int = 7,
                                source: str = "all") -> dict:
    """统一入口：双源拉取 + 入库。

    source: nvd / osv / all
    返回 {"nvd": {...}, "osv": {...}, "added": int, "updated": int}
    """
    all_cves: list[dict] = []
    result: dict[str, Any] = {"nvd": {}, "osv": {}}

    if source in ("nvd", "all"):
        try:
            nvd_cves = await fetch_nvd_cves(
                api_key=getattr(settings, "nvd_api_key", "") or "",
                days=days,
                max_results=getattr(settings, "cve_fetch_max", 500),
            )
            all_cves.extend(nvd_cves)
            result["nvd"] = {"count": len(nvd_cves)}
        except Exception as e:  # noqa: BLE001
            result["nvd"] = {"error": str(e)}
            log.warning("NVD 拉取异常: %s", e)

    if source in ("osv", "all"):
        try:
            osv_cves = await fetch_osv_cves(
                days=days,
                max_results=getattr(settings, "cve_fetch_max", 500),
            )
            all_cves.extend(osv_cves)
            result["osv"] = {"count": len(osv_cves)}
        except Exception as e:  # noqa: BLE001
            result["osv"] = {"error": str(e)}
            log.warning("OSV 拉取异常: %s", e)

    if not all_cves:
        result["added"] = 0
        result["updated"] = 0
        return result

    merge = merge_and_save_cves(all_cves, db)
    result["added"] = merge["added"]
    result["updated"] = merge["updated"]
    if merge["errors"]:
        result["errors"] = merge["errors"]
    return result
