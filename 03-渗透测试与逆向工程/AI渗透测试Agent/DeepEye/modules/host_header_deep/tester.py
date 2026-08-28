"""Deep Host Header Injection / Password-Reset Poisoning tester."""
from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from utils.logger import get_logger

logger = get_logger(__name__)

_EVIL_HOST = "evil-poison.example"
_RESET_PATH_RE = re.compile(r"/(forgot|reset|password|recovery)", re.IGNORECASE)


class HostHeaderDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        parsed = urlparse(url)
        is_reset_path = bool(_RESET_PATH_RE.search(parsed.path))

        # 1. Basic Host header injection
        vulns.extend(self._probe(url, "Host", _EVIL_HOST, is_reset_path))

        # 2. X-Forwarded-Host
        vulns.extend(self._probe(url, "X-Forwarded-Host", _EVIL_HOST, is_reset_path))

        # 3. X-Host
        vulns.extend(self._probe(url, "X-Host", _EVIL_HOST, is_reset_path))

        # 4. X-Original-URL (some proxies use this to reconstruct original URL)
        vulns.extend(self._probe(url, "X-Original-URL", f"http://{_EVIL_HOST}/", is_reset_path))

        # 5. X-Rewrite-URL
        vulns.extend(self._probe(url, "X-Rewrite-URL", f"http://{_EVIL_HOST}/", is_reset_path))

        # 6. Forwarded (RFC 7239)
        vulns.extend(self._probe(url, "Forwarded", f"host={_EVIL_HOST}", is_reset_path))

        # 7. Absolute-URL host confusion in path (some proxies forward this to backend)
        abs_url = f"{parsed.scheme}://{_EVIL_HOST}{parsed.path}"
        if parsed.query:
            abs_url += f"?{parsed.query}"
        vulns.extend(self._probe(url, "X-Original-URL", abs_url, is_reset_path, label="Absolute-URL host confusion"))

        # 8. Userinfo confusion: Host header with userinfo (evil.com@target.com)
        userinfo_host = f"{_EVIL_HOST}@{parsed.hostname}"
        vulns.extend(self._probe(url, "Host", userinfo_host, is_reset_path, label="Host userinfo confusion"))

        return vulns

    def _probe(
        self,
        url: str,
        header: str,
        value: str,
        is_reset_path: bool,
        label: Optional[str] = None,
    ) -> List[Dict]:
        out = []
        try:
            resp = self.http_client.get(url, headers={header: value})
            if not resp:
                return out
            body = getattr(resp, "text", "") or ""
            headers = {k.lower(): v for k, v in dict(getattr(resp, "headers", {}) or {}).items()}

            reflected_in_body = _EVIL_HOST in body
            reflected_in_headers = any(_EVIL_HOST in str(v) for v in headers.values())

            if reflected_in_body or reflected_in_headers:
                sev = "high" if is_reset_path else "medium"
                evidence_parts = []
                if reflected_in_body:
                    evidence_parts.append("reflected in response body")
                if reflected_in_headers:
                    matching = [f"{k}={v[:120]}" for k, v in headers.items() if _EVIL_HOST in str(v)]
                    evidence_parts.append(f"reflected in headers: {', '.join(matching)}")

                out.append(
                    {
                        "type": label or f"Host Header Injection ({header})",
                        "severity": sev,
                        "url": url,
                        "parameter": header,
                        "payload": value,
                        "evidence": "; ".join(evidence_parts),
                        "description": (
                            f"The {header} header value was reflected by the server. "
                            "This can lead to cache poisoning, password-reset poisoning, or SSRF."
                        ),
                        "remediation": (
                            "Validate and whitelist the Host header; do not use attacker-controlled "
                            "headers (X-Forwarded-Host, X-Host, etc.) to build sensitive URLs."
                        ),
                    }
                )
        except Exception as e:
            logger.debug(f"HostHeaderDeep probe failed for {header}={value}: {e}")
        return out
