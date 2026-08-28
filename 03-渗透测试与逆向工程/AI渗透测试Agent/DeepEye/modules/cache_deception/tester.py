"""Web cache deception: path tricks + cache-header heuristics."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from utils.logger import get_logger

logger = get_logger(__name__)

_TRICKS = (
    "/.css",
    "%2f.css",
    "/;.css",
    "/..%2fstatic/app.css",
    "/.js",
    "%2f.js",
    "/;.js",
    "/.png",
    "/static.css",
    "/nonexistent.css",
    "?cb=.css",
    "/..;/app.css",
)


class CacheDeceptionTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        parsed = urlparse(url)
        if not parsed.path or parsed.path == "/":
            return vulns
        base = self.http_client.get(url)
        if not base:
            return vulns
        base_body = getattr(base, "text", "") or ""
        base_len = len(base_body)
        base_h = {k.lower(): str(v) for k, v in dict(getattr(base, "headers", {}) or {}).items()}

        candidates = [url.rstrip("/") + t if not t.startswith("?") else url + t for t in _TRICKS]
        candidates.append(urljoin(url, "account/settings/static.css"))

        for t in candidates[:12]:
            try:
                resp = self.http_client.get(t)
                if not resp:
                    continue
                body = getattr(resp, "text", "") or ""
                st = getattr(resp, "status_code", 0)
                h = {k.lower(): str(v) for k, v in dict(getattr(resp, "headers", {}) or {}).items()}
                cacheable = any(
                    x in (h.get("cache-control") or "").lower()
                    for x in ("public", "max-age", "s-maxage")
                ) or h.get("x-cache") or h.get("cf-cache-status") or h.get("age")
                private_markers = ("logout", "password", "session", "csrf", "email", "token", "account")
                looks_private = any(k in body.lower() for k in private_markers)
                similar = st == 200 and abs(len(body) - base_len) < 300 and base_len > 50
                if similar and looks_private:
                    sev = "high" if cacheable else "medium"
                    vulns.append({
                        "type": "Web Cache Deception",
                        "severity": sev,
                        "url": t,
                        "parameter": "path",
                        "payload": t,
                        "evidence": (
                            f"Sensitive body on static-looking path ({len(body)} bytes); "
                            f"cache headers={h.get('cache-control') or h.get('x-cache') or h.get('cf-cache-status') or 'none'}"
                        ),
                        "description": "Path normalization may cache private responses as static assets",
                        "remediation": "Normalize paths before cache key; never cache authenticated HTML as static",
                    })
                    break
            except Exception as e:
                logger.debug(f"cache deception: {e}")

        # Vary / cookie unkeyed heuristic on base
        if "cookie" not in (base_h.get("vary") or "").lower() and base_h.get("set-cookie"):
            vulns.append({
                "type": "Cache Possibly Unkeyed on Cookie",
                "severity": "info",
                "url": url,
                "parameter": "Vary",
                "payload": "",
                "evidence": f"Vary={base_h.get('vary')}; Set-Cookie present",
                "description": "Response sets cookies but Vary may omit Cookie (cache key risk)",
                "remediation": "Include Cookie in Vary or use Cache-Control: private for auth responses",
            })
        return vulns
