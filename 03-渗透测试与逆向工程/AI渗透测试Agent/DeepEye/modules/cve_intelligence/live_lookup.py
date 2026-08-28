"""Live CVE / exploit reference lookup via public APIs (NVD, GitHub).

Original Deep Eye implementation. Uses NIST NVD REST 2.0 and GitHub Search
public endpoints only — not derived from third-party tool source.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from utils.logger import get_logger

logger = get_logger(__name__)

_NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.I)

# simple in-process throttle / cache
_last_nvd = 0.0
_cache: Dict[str, Any] = {}


def nvd_detail_url(cve_id: str) -> str:
    return f"https://nvd.nist.gov/vuln/detail/{cve_id}"


def exploitdb_search_url(cve_id: str) -> str:
    return f"https://www.exploit-db.com/search?cve={quote_plus(cve_id)}"


def github_poc_search_url(cve_id: str) -> str:
    return f"https://github.com/search?q={quote_plus(cve_id)}+exploit+OR+poc&type=repositories"


def attach_reference_links(cve_id: str) -> Dict[str, str]:
    cid = (cve_id or "").strip().upper()
    if not cid.startswith("CVE-"):
        return {}
    return {
        "nvd": nvd_detail_url(cid),
        "exploit_db": exploitdb_search_url(cid),
        "github_poc": github_poc_search_url(cid),
    }


def extract_cve_ids(text: str) -> List[str]:
    return list(dict.fromkeys(m.group(0).upper() for m in _CVE_RE.finditer(text or "")))


def _throttle(min_interval: float = 0.6) -> None:
    global _last_nvd
    now = time.time()
    wait = min_interval - (now - _last_nvd)
    if wait > 0:
        time.sleep(wait)
    _last_nvd = time.time()


def nvd_search_keyword(
    keyword: str,
    max_results: int = 5,
    api_key: str = "",
    session=None,
) -> List[Dict[str, Any]]:
    """Query NVD 2.0 keywordSearch. Returns normalized CVE dicts."""
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    cache_key = f"kw:{keyword}:{max_results}"
    if cache_key in _cache:
        return list(_cache[cache_key])

    try:
        import requests
    except ImportError:
        logger.debug("requests not available for NVD live lookup")
        return []

    headers = {"User-Agent": "Deep-Eye/1.4 (CVE intelligence; authorized security testing)"}
    if api_key:
        headers["apiKey"] = api_key
    params = {
        "keywordSearch": keyword[:200],
        "resultsPerPage": max(1, min(20, int(max_results))),
    }
    try:
        _throttle()
        sess = session or requests
        resp = sess.get(_NVD_URL, params=params, headers=headers, timeout=25)
        if getattr(resp, "status_code", 0) != 200:
            logger.debug(f"NVD keyword search HTTP {getattr(resp, 'status_code', '?')}")
            return []
        data = resp.json() if hasattr(resp, "json") else {}
        out = [_normalize_nvd_item(w) for w in (data.get("vulnerabilities") or [])]
        out = [x for x in out if x.get("cve_id")]
        _cache[cache_key] = out
        return list(out)
    except Exception as e:
        logger.debug(f"NVD keyword search failed: {e}")
        return []


def nvd_get_cve(
    cve_id: str,
    api_key: str = "",
    session=None,
) -> Optional[Dict[str, Any]]:
    cid = (cve_id or "").strip().upper()
    if not cid.startswith("CVE-"):
        return None
    cache_key = f"id:{cid}"
    if cache_key in _cache:
        return dict(_cache[cache_key])
    try:
        import requests
    except ImportError:
        return None
    headers = {"User-Agent": "Deep-Eye/1.4 (CVE intelligence; authorized security testing)"}
    if api_key:
        headers["apiKey"] = api_key
    try:
        _throttle()
        sess = session or requests
        resp = sess.get(
            _NVD_URL,
            params={"cveId": cid},
            headers=headers,
            timeout=25,
        )
        if getattr(resp, "status_code", 0) != 200:
            return None
        data = resp.json() if hasattr(resp, "json") else {}
        items = data.get("vulnerabilities") or []
        if not items:
            return None
        norm = _normalize_nvd_item(items[0])
        if norm.get("cve_id"):
            _cache[cache_key] = norm
        return norm
    except Exception as e:
        logger.debug(f"NVD CVE fetch failed: {e}")
        return None


def github_search_repos(
    keyword: str,
    max_results: int = 5,
    token: str = "",
    session=None,
) -> List[Dict[str, Any]]:
    """GitHub repository search for exploit/POC-related repos."""
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    cache_key = f"gh:{keyword}:{max_results}"
    if cache_key in _cache:
        return list(_cache[cache_key])
    try:
        import requests
    except ImportError:
        return []
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Deep-Eye/1.4",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = {
        "q": f"{keyword} exploit OR poc OR vulnerability",
        "sort": "stars",
        "order": "desc",
        "per_page": max(1, min(10, int(max_results))),
    }
    try:
        sess = session or requests
        resp = sess.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
            timeout=20,
        )
        if getattr(resp, "status_code", 0) != 200:
            return []
        data = resp.json() if hasattr(resp, "json") else {}
        out = []
        for repo in data.get("items") or []:
            out.append(
                {
                    "full_name": repo.get("full_name"),
                    "stars": repo.get("stargazers_count"),
                    "url": repo.get("html_url"),
                    "description": (repo.get("description") or "")[:200],
                    "language": repo.get("language"),
                }
            )
        _cache[cache_key] = out
        return list(out)
    except Exception as e:
        logger.debug(f"GitHub search failed: {e}")
        return []


def _normalize_nvd_item(wrapper: Dict) -> Dict[str, Any]:
    vuln = (wrapper or {}).get("cve") or wrapper or {}
    cve_id = vuln.get("id") or ""
    description = ""
    for desc in vuln.get("descriptions") or []:
        if (desc.get("lang") or "").lower() == "en":
            description = desc.get("value") or ""
            break
    if not description and vuln.get("descriptions"):
        description = (vuln["descriptions"][0] or {}).get("value") or ""

    metrics = vuln.get("metrics") or {}
    score, severity, vector = None, None, None
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        arr = metrics.get(key) or []
        if not arr:
            continue
        cvss = (arr[0] or {}).get("cvssData") or {}
        score = cvss.get("baseScore")
        severity = cvss.get("baseSeverity") or (arr[0] or {}).get("baseSeverity")
        vector = cvss.get("vectorString")
        break

    refs = []
    for ref in (vuln.get("references") or [])[:8]:
        u = (ref or {}).get("url")
        if u:
            refs.append(u)

    links = attach_reference_links(cve_id) if cve_id else {}
    return {
        "cve_id": cve_id,
        "description": description[:500],
        "severity": severity,
        "cvss_score": score,
        "cvss_vector": vector,
        "published": (vuln.get("published") or "")[:10],
        "references": refs,
        "links": links,
    }


def keyword_from_finding(vulnerability: Dict) -> str:
    """Build a short NVD keyword from a finding dict."""
    parts = [
        vulnerability.get("type") or "",
        vulnerability.get("parameter") or "",
    ]
    evidence = str(vulnerability.get("evidence") or "")[:80]
    # prefer explicit CVE ids in evidence
    ids = extract_cve_ids(evidence + " " + str(vulnerability.get("description") or ""))
    if ids:
        return ids[0]
    # strip noise words
    raw = " ".join(parts)
    raw = re.sub(r"[^\w\s\-\.]", " ", raw)
    tokens = [t for t in raw.split() if len(t) > 2][:6]
    return " ".join(tokens)[:120]
