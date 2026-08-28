"""Finding fingerprint + dedupe for report/diff identity."""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse


def normalize_path(url: str) -> str:
    try:
        p = urlparse(url or "")
        path = p.path or "/"
        if path.endswith("/") and len(path) > 1:
            path = path.rstrip("/")
        return f"{(p.scheme or '').lower()}://{(p.netloc or '').lower()}{path}"
    except Exception:
        return url or ""


def root_cause_hint(vuln: Dict) -> str:
    t = str(vuln.get("type", "")).lower()
    evidence = str(vuln.get("evidence", ""))[:120]
    payload = str(vuln.get("payload", ""))[:80]
    return re.sub(r"\s+", " ", f"{t}|{payload}|{evidence}").strip()


def fingerprint(vuln: Dict) -> str:
    """Stable hash: type + path + parameter + root_cause hint."""
    raw = "|".join(
        [
            str(vuln.get("type", "")),
            normalize_path(str(vuln.get("url", ""))),
            str(vuln.get("parameter", "")),
            root_cause_hint(vuln),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def dedupe_findings(vulns: List[Dict], prefer_higher_severity: bool = True) -> List[Dict]:
    """Collapse duplicates by fingerprint; keep highest severity."""
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    best: Dict[str, Dict] = {}
    order: List[str] = []
    for v in vulns:
        if not isinstance(v, dict):
            continue
        fp = v.get("fingerprint") or fingerprint(v)
        v = dict(v)
        v["fingerprint"] = fp
        prev = best.get(fp)
        if prev is None:
            best[fp] = v
            order.append(fp)
            continue
        if prefer_higher_severity:
            if rank.get(str(v.get("severity", "info")).lower(), 0) > rank.get(
                str(prev.get("severity", "info")).lower(), 0
            ):
                best[fp] = v
        else:
            best[fp] = v
    return [best[fp] for fp in order]


def identity_tuple(vuln: Dict) -> Tuple[str, str, str]:
    return (
        str(vuln.get("type", "")),
        normalize_path(str(vuln.get("url", ""))),
        str(vuln.get("parameter", "")),
    )
