"""Advanced open-redirect fuzzer with protocol-relative, JS/data schemes, and auth-bypass payloads."""
from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

# Parameters commonly used for redirects
_REDIRECT_PARAMS = [
    "url",
    "next",
    "redirect",
    "return",
    "ReturnUrl",
    "redirect_uri",
    "continue",
    "goto",
    "RelayState",
    "dest",
    "destination",
    "redir",
    "rurl",
    "returnUrl",
]

# Advanced payloads beyond the toy _check_open_redirect
_PAYLOADS = [
    "//evil.example",
    "https://evil.example",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "https:\\\\evil.example",
    "//evil.example/%2f..",
    "victim.com@evil.example",
]

# Detection patterns
_EVIL_DOMAIN = "evil.example"
_JAVASCRIPT_SCHEME = re.compile(r"javascript\s*:", re.IGNORECASE)
_DATA_SCHEME = re.compile(r"data\s*:", re.IGNORECASE)
_META_REFRESH = re.compile(
    r'<meta[^>]+http-equiv\s*=\s*["\']?refresh["\']?[^>]*>',
    re.IGNORECASE,
)
_META_URL = re.compile(r'url\s*=\s*([^"\'>\s]+)', re.IGNORECASE)
_BODY_LOCATION = re.compile(r'location\s*=\s*["\']?([^"\'>\s]+)', re.IGNORECASE)


class OpenRedirectDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        vulns: List[Dict] = []
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        if not params:
            return vulns

        for param_name in params.keys():
            if not any(rp == param_name for rp in _REDIRECT_PARAMS):
                continue
            for payload in _PAYLOADS:
                test_params = {k: list(v) for k, v in params.items()}
                test_params[param_name] = [payload]
                test_query = urlencode(test_params, doseq=True)
                test_url = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        test_query,
                        parsed.fragment,
                    )
                )
                try:
                    response = self.http_client.get(test_url, allow_redirects=False)
                except Exception as e:
                    logger.debug(f"Open redirect deep probe failed for {test_url}: {e}")
                    continue
                if not response:
                    continue
                finding = self._analyze(response, url, param_name, payload)
                if finding:
                    vulns.append(finding)
        return vulns

    def _analyze(self, response, original_url: str, param: str, payload: str) -> Optional[Dict]:
        status = getattr(response, "status_code", 0)
        headers = getattr(response, "headers", {}) or {}
        body = getattr(response, "text", "") or ""
        location = headers.get("Location", "")

        # 3xx with Location containing evil domain
        if status in (301, 302, 303, 307, 308) and _EVIL_DOMAIN in location:
            return {
                "type": "Open Redirect (Deep)",
                "severity": "medium",
                "url": original_url,
                "parameter": param,
                "payload": payload,
                "evidence": f"Redirect to {location}",
                "description": "Open redirect allows attackers to redirect users to malicious sites",
                "remediation": "Validate redirect URLs against an explicit whitelist",
            }

        # Location header with javascript: or data: scheme
        if _JAVASCRIPT_SCHEME.search(location) or _DATA_SCHEME.search(location):
            return {
                "type": "Open Redirect (Deep) — Client-side Scheme",
                "severity": "high",
                "url": original_url,
                "parameter": param,
                "payload": payload,
                "evidence": f"Location header contains dangerous scheme: {location}",
                "description": "Redirect response includes javascript:/data: scheme in Location header",
                "remediation": "Reject javascript:/data: schemes in redirect targets; use strict URL validation",
            }

        # Body meta refresh pointing to evil domain
        if _META_REFRESH.search(body):
            for m in _META_URL.finditer(body):
                if _EVIL_DOMAIN in m.group(1):
                    return {
                        "type": "Open Redirect (Deep) — Meta Refresh",
                        "severity": "medium",
                        "url": original_url,
                        "parameter": param,
                        "payload": payload,
                        "evidence": f"Meta refresh redirects to {m.group(1)}",
                        "description": "Response body contains meta refresh to external domain",
                        "remediation": "Validate redirect URLs against an explicit whitelist",
                    }

        # Body location= pointing to evil domain
        for m in _BODY_LOCATION.finditer(body):
            if _EVIL_DOMAIN in m.group(1):
                return {
                    "type": "Open Redirect (Deep) — Body Location",
                    "severity": "medium",
                    "url": original_url,
                    "parameter": param,
                    "payload": payload,
                    "evidence": f"Body location assignment to {m.group(1)}",
                    "description": "Response body contains location assignment to external domain",
                    "remediation": "Validate redirect URLs against an explicit whitelist",
                }

        return None
