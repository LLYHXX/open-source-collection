"""IDOR / BOLA: sequential ID, UUID-ish, base64, header role swap."""
from __future__ import annotations

import base64
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_ID_RE = re.compile(r"(?<=[=/])(\d{1,12})(?=/|$|&|\?)")
_UUID_RE = re.compile(
    r"(?<=[=/])([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?=/|$|&|\?)"
)
_B64_RE = re.compile(r"(?<=[=/])([A-Za-z0-9+/]{8,}={0,2})(?=/|$|&|\?)")


class IDORTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config
        self.cfg = config.get("idor") or {}
        self.max_swaps = int(self.cfg.get("max_swaps", 8))

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        baseline = (context or {}).get("response")
        if baseline is None:
            baseline = self.http_client.get(url)
        if not baseline:
            return vulns
        base_status = getattr(baseline, "status_code", 0)
        base_body = getattr(baseline, "text", "") or ""
        base_len = len(base_body)
        if base_status not in (200, 201):
            return vulns

        for mut_url, param in self._mutate_ids(url)[: self.max_swaps]:
            try:
                resp = self.http_client.get(mut_url)
                if not resp:
                    continue
                st = getattr(resp, "status_code", 0)
                body = getattr(resp, "text", "") or ""
                ln = len(body)
                if st == 200 and abs(ln - base_len) > 50:
                    vulns.append({
                        "type": "Potential IDOR / BOLA",
                        "severity": "high",
                        "url": mut_url,
                        "parameter": param,
                        "payload": mut_url,
                        "evidence": f"status={st} len={ln} vs baseline len={base_len}",
                        "description": "Object ID swap returned different content with 200",
                        "remediation": "Enforce object-level authorization on every request",
                    })
            except Exception as e:
                logger.debug(f"IDOR probe failed: {e}")

        # horizontal: replay with alternate role headers if session provides them
        roles = (context or {}).get("alt_headers") or self.cfg.get("alt_headers") or []
        for hdrs in roles[:2]:
            if not isinstance(hdrs, dict):
                continue
            try:
                resp = self.http_client.get(url, headers=hdrs)
                if not resp:
                    continue
                st = getattr(resp, "status_code", 0)
                body = getattr(resp, "text", "") or ""
                if st == 200 and abs(len(body) - base_len) > 80 and body != base_body:
                    vulns.append({
                        "type": "Potential IDOR via Role Header Swap",
                        "severity": "high",
                        "url": url,
                        "parameter": "headers",
                        "payload": str(list(hdrs.keys())),
                        "evidence": f"alt role status={st} len={len(body)} vs {base_len}",
                        "description": "Alternate auth headers returned different object data",
                        "remediation": "Bind object access to authenticated principal, not client-supplied role headers",
                    })
            except Exception as e:
                logger.debug(f"IDOR role swap: {e}")
        return vulns

    def _mutate_ids(self, url: str) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        parsed = urlparse(url)
        for m in _ID_RE.finditer(parsed.path):
            n = int(m.group(1))
            for delta in (1, -1, 2, 999, 1000):
                nn = max(1, n + delta)
                new_path = parsed.path[: m.start(1)] + str(nn) + parsed.path[m.end(1) :]
                out.append((urlunparse(parsed._replace(path=new_path)), f"path:{m.group(1)}"))
        for m in _UUID_RE.finditer(parsed.path + ("?" + parsed.query if parsed.query else "")):
            raw = m.group(1)
            # flip last hex nibble
            try:
                last = int(raw[-1], 16)
                flipped = raw[:-1] + format((last + 1) % 16, "x")
            except Exception:
                continue
            if raw in parsed.path:
                new_path = parsed.path.replace(raw, flipped, 1)
                out.append((urlunparse(parsed._replace(path=new_path)), f"uuid:{raw[:8]}"))
            elif raw in parsed.query:
                out.append((
                    urlunparse(parsed._replace(query=parsed.query.replace(raw, flipped, 1))),
                    f"uuid:{raw[:8]}",
                ))
        for m in _B64_RE.finditer(parsed.path):
            tok = m.group(1)
            if len(tok) > 40:
                continue
            try:
                pad = "=" * (-len(tok) % 4)
                dec = base64.b64decode(tok + pad)
                if dec.isdigit() or (len(dec) <= 8 and dec.isalnum()):
                    alt = base64.b64encode(str(int(dec.decode() or "1") + 1).encode()).decode().rstrip("=")
                    new_path = parsed.path[: m.start(1)] + alt + parsed.path[m.end(1) :]
                    out.append((urlunparse(parsed._replace(path=new_path)), f"b64:{tok[:8]}"))
            except Exception:
                pass
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for key, vals in qs.items():
            if not vals:
                continue
            v = vals[0]
            if v.isdigit():
                n = int(v)
                for delta in (1, -1, 2, 999):
                    qs2 = {k: list(vv) for k, vv in qs.items()}
                    qs2[key] = [str(max(1, n + delta))]
                    out.append((
                        urlunparse(parsed._replace(query=urlencode(qs2, doseq=True))),
                        key,
                    ))
            elif _UUID_RE.fullmatch(v):
                try:
                    last = int(v[-1], 16)
                    flipped = v[:-1] + format((last + 1) % 16, "x")
                    qs2 = {k: list(vv) for k, vv in qs.items()}
                    qs2[key] = [flipped]
                    out.append((
                        urlunparse(parsed._replace(query=urlencode(qs2, doseq=True))),
                        key,
                    ))
                except Exception:
                    pass
        return out
